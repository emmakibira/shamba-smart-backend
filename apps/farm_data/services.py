import requests
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import WeatherCache, SensorDevice, SensorReading, SensorAlert

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data from Open-Meteo (FREE, no API key required)"""
    
    BASE_URL = getattr(settings, 'OPEN_METEO_BASE_URL', 'https://api.open-meteo.com/v1')
    
    @classmethod
    def get_weather(cls, latitude, longitude):
        """Get current weather for location with caching"""
        # Check cache first
        try:
            cache = WeatherCache.objects.get(
                latitude=float(latitude),
                longitude=float(longitude)
            )
            if cache.is_fresh():
                logger.info(f"Returning cached weather for {latitude}, {longitude}")
                return cache.weather_data
            else:
                cache.delete()
        except WeatherCache.DoesNotExist:
            pass
        
        # Fetch from Open-Meteo API (completely free, no API key)
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current_weather': 'true',
            'hourly': 'temperature_2m,relativehumidity_2m,precipitation,wind_speed_10m',
            'timezone': 'Africa/Dar_es_Salaam',
            'forecast_days': 7
        }
        
        try:
            logger.info(f"Fetching REAL weather from Open-Meteo for {latitude}, {longitude}")
            response = requests.get(f"{cls.BASE_URL}/forecast", params=params, timeout=10)
            response.raise_for_status()
            weather_data = response.json()
            
            # Format to match expected structure for compatibility
            formatted_data = {
                'current_weather': weather_data.get('current_weather', {}),
                'hourly': weather_data.get('hourly', {}),
                'daily': cls._extract_daily_forecast(weather_data),
                'weather': [{'main': cls._get_weather_condition(weather_data.get('current_weather', {}))}]
            }
            
            # Cache for 30 minutes
            WeatherCache.objects.update_or_create(
                latitude=float(latitude),
                longitude=float(longitude),
                defaults={'weather_data': formatted_data}
            )
            
            return formatted_data
        except Exception as e:
            logger.error(f"Error fetching weather from Open-Meteo: {str(e)}")
            return None
    
    @classmethod
    def get_weather_forecast(cls, latitude, longitude, days=5):
        """Get weather forecast from Open-Meteo"""
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode',
            'timezone': 'Africa/Dar_es_Salaam',
            'forecast_days': days
        }
        
        try:
            response = requests.get(f"{cls.BASE_URL}/forecast", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse daily forecast
            daily_forecasts = []
            daily_data = data.get('daily', {})
            times = daily_data.get('time', [])
            
            # Weather code mapping (WMO codes)
            weather_codes = {
                0: 'Clear sky',
                1: 'Mainly clear',
                2: 'Partly cloudy',
                3: 'Overcast',
                45: 'Foggy',
                51: 'Light drizzle',
                61: 'Rain',
                71: 'Snow fall',
                80: 'Rain showers'
            }
            
            for i, date in enumerate(times):
                weather_code = daily_data.get('weathercode', [0])[i] if i < len(daily_data.get('weathercode', [])) else 0
                daily_forecasts.append({
                    'date': date,
                    'temp_min': daily_data.get('temperature_2m_min', [0])[i] if i < len(daily_data.get('temperature_2m_min', [])) else 0,
                    'temp_max': daily_data.get('temperature_2m_max', [0])[i] if i < len(daily_data.get('temperature_2m_max', [])) else 0,
                    'precipitation': daily_data.get('precipitation_sum', [0])[i] if i < len(daily_data.get('precipitation_sum', [])) else 0,
                    'description': weather_codes.get(weather_code, 'Unknown'),
                    'rainfall_probability': min(100, int(daily_data.get('precipitation_sum', [0])[i] * 10)) if i < len(daily_data.get('precipitation_sum', [])) else 0,
                })
            
            return daily_forecasts
        except Exception as e:
            logger.error(f"Error fetching forecast from Open-Meteo: {str(e)}")
            return []
    
    @classmethod
    def _extract_daily_forecast(cls, weather_data):
        """Extract daily forecast from Open-Meteo response"""
        daily = weather_data.get('daily', {})
        forecasts = []
        times = daily.get('time', [])
        
        for i, date in enumerate(times):
            precipitation_sum = (
                daily.get('precipitation_sum', [0])[i]
                if i < len(daily.get('precipitation_sum', []))
                else 0
            )
            
            # Keep both field names for compatibility:
            # - `precipitation` used by some UI/components
            # - `precipitation_sum` used by get_farming_advisory() rainfall extraction
            forecasts.append({
                'date': date,
                'temp_max': daily.get('temperature_2m_max', [0])[i] if i < len(daily.get('temperature_2m_max', [])) else 0,
                'temp_min': daily.get('temperature_2m_min', [0])[i] if i < len(daily.get('temperature_2m_min', [])) else 0,
                'precipitation': precipitation_sum,
                'precipitation_sum': precipitation_sum,
            })
        
        return forecasts
    
    @classmethod
    def _get_weather_condition(cls, current_weather):
        """Map Open-Meteo weather code to condition string"""
        weather_code = current_weather.get('weathercode', 0)
        
        if weather_code in [0, 1]:
            return 'Clear'
        elif weather_code in [2, 3]:
            return 'Clouds'
        elif weather_code in [45, 48]:
            return 'Fog'
        elif weather_code in [51, 53, 55, 56, 57]:
            return 'Drizzle'
        elif weather_code in [61, 63, 65, 66, 67]:
            return 'Rain'
        elif weather_code in [71, 73, 75, 77]:
            return 'Snow'
        elif weather_code in [80, 81, 82]:
            return 'Rain'
        elif weather_code >= 95:
            return 'Thunderstorm'
        else:
            return 'Unknown'
    
    @classmethod
    def get_farming_advisory(cls, weather_data, crop_type='general'):
        """Generate farming advisory based on weather"""
        if not weather_data:
            return cls._get_default_advisory()
        
        current = weather_data.get('current_weather', {})
        temperature = current.get('temperature', 25)
        wind_speed = current.get('windspeed', 10)
        weather_code = current.get('weathercode', 0)
        
        # Determine conditions
        is_rainy = weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]
        is_clear = weather_code in [0, 1]
        is_cloudy = weather_code in [2, 3]
        is_storm = weather_code >= 95
        
        # Generate advisory
        advisory_text = "Moderate weather. Continue regular farming activities."
        
        if is_storm:
            advisory_text = "Thunderstorms expected. Postpone field activities. Secure equipment and shelter animals."
        elif is_rainy:
            advisory_text = "Rain expected. Good for watering. Ensure proper drainage to prevent waterlogging. Consider postponing fertilizer application."
        elif temperature > 35:
            advisory_text = f"High temperature ({temperature:.0f}°C). Increase irrigation frequency. Watch for pest activity. Provide shade for sensitive crops."
        elif temperature < 15:
            advisory_text = f"Cool temperature ({temperature:.0f}°C). Protect sensitive crops from cold. Delay planting if expecting frost."
        elif is_clear:
            advisory_text = "Clear skies. Good for field activities like spraying and harvesting. Monitor soil moisture."
        elif wind_speed > 20:
            advisory_text = f"Strong winds ({wind_speed:.0f} km/h). Avoid spraying. Check for wind damage to tall crops."
        
        return {
            'current_weather': 'rainy' if is_rainy else 'storm' if is_storm else 'clear' if is_clear else 'cloudy',
            'temperature': round(temperature),
            'humidity': 65,  # Open-Meteo provides humidity in hourly data
            'wind_speed': round(wind_speed),
            'rainfall': weather_data.get('daily', {}).get('precipitation_sum', [0])[0] if weather_data.get('daily') else 0,
            'advisory': advisory_text,
            'weather_code': weather_code
        }
    
    @classmethod
    def _get_default_advisory(cls):
        """Return default advisory when API fails"""
        return {
            'current_weather': 'unknown',
            'temperature': 25,
            'humidity': 60,
            'wind_speed': 10,
            'rainfall': 0,
            'advisory': 'Unable to fetch live weather. Showing default values.'
        }


class SensorService:
    """Service for managing sensor devices and readings"""
    
    @staticmethod
    def add_sensor_reading(sensor_id, value):
        """Add a new sensor reading and check for alerts"""
        try:
            sensor = SensorDevice.objects.get(id=sensor_id)
            
            # Create reading
            reading = SensorReading.objects.create(
                sensor=sensor,
                value=value
            )
            
            # Update sensor last seen
            sensor.last_seen = timezone.now()
            if sensor.status != 'active':
                sensor.status = 'active'
            sensor.save()
            
            # Check thresholds
            SensorService.check_thresholds(sensor, reading, value)
            
            return reading
        except SensorDevice.DoesNotExist:
            logger.error(f"Sensor {sensor_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error adding sensor reading: {str(e)}")
            return None
    
    @staticmethod
    def check_thresholds(sensor, reading, value):
        """Check if reading exceeds thresholds and create alerts"""
        alerts_created = []
        
        if sensor.min_threshold is not None and value < sensor.min_threshold:
            severity = 'critical' if value < (sensor.min_threshold * 0.8) else 'warning'
            alert = SensorAlert.objects.create(
                sensor=sensor,
                reading=reading,
                severity=severity,
                message=f"{sensor.name} reading below threshold: {value} {sensor.unit}",
                threshold_exceeded='min',
                expected_value=sensor.min_threshold,
                actual_value=value
            )
            alerts_created.append(alert)
        
        if sensor.max_threshold is not None and value > sensor.max_threshold:
            severity = 'critical' if value > (sensor.max_threshold * 1.2) else 'warning'
            alert = SensorAlert.objects.create(
                sensor=sensor,
                reading=reading,
                severity=severity,
                message=f"{sensor.name} reading above threshold: {value} {sensor.unit}",
                threshold_exceeded='max',
                expected_value=sensor.max_threshold,
                actual_value=value
            )
            alerts_created.append(alert)
        
        return alerts_created
    
    @staticmethod
    def get_latest_readings(sensor_id, hours=24):
        """Get sensor readings from last N hours"""
        try:
            sensor = SensorDevice.objects.get(id=sensor_id)
            cutoff_time = timezone.now() - timedelta(hours=hours)
            
            readings = SensorReading.objects.filter(
                sensor=sensor,
                timestamp__gte=cutoff_time
            ).order_by('timestamp')
            
            return readings
        except SensorDevice.DoesNotExist:
            return None
    
    @staticmethod
    def get_sensor_summary(user):
        """Get summary of all user's sensors"""
        sensors = SensorDevice.objects.filter(user=user)
        summary = {
            'total_sensors': sensors.count(),
            'active_sensors': sensors.filter(status='active').count(),
            'inactive_sensors': sensors.filter(status='inactive').count(),
            'error_sensors': sensors.filter(status='error').count(),
            'recent_readings': {},
            'active_alerts': {}
        }
        
        for sensor in sensors:
            # Latest reading
            latest_reading = sensor.readings.latest('timestamp') if sensor.readings.exists() else None
            summary['recent_readings'][sensor.id] = {
                'sensor_name': sensor.name,
                'value': latest_reading.value if latest_reading else None,
                'timestamp': latest_reading.timestamp if latest_reading else None,
                'unit': sensor.unit
            }
            
            # Active alerts
            active_alerts = sensor.alerts.filter(is_resolved=False)
            summary['active_alerts'][sensor.id] = {
                'count': active_alerts.count(),
                'alerts': [
                    {
                        'severity': alert.severity,
                        'message': alert.message,
                        'created_at': alert.created_at
                    }
                    for alert in active_alerts[:5]  # Latest 5 alerts
                ]
            }
        
        return summary


class MarketService:
    """Service for market-related operations"""
    
    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km
    
    @staticmethod
    def find_nearby_markets(user_latitude, user_longitude, radius_km=50):
        """Find markets within radius"""
        from .models import Market
        
        nearby_markets = []
        all_markets = Market.objects.all()
        
        for market in all_markets:
            distance = MarketService.haversine_distance(
                float(user_latitude),
                float(user_longitude),
                float(market.latitude),
                float(market.longitude)
            )
            
            if distance <= radius_km:
                nearby_markets.append({
                    'market': market,
                    'distance': distance
                })
        
        # Sort by distance
        nearby_markets.sort(key=lambda x: x['distance'])
        return nearby_markets