import requests
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import WeatherCache, SensorDevice, SensorReading, SensorAlert

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data from OpenWeatherMap (free tier)"""
    
    API_KEY = getattr(settings, 'OPENWEATHER_API_KEY', '')
    CURRENT_WEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'
    FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'
    
    @classmethod
    def get_weather(cls, latitude, longitude):
        """Get weather for location with caching"""
        # Check cache first
        try:
            cache = WeatherCache.objects.get(
                latitude=float(latitude),
                longitude=float(longitude)
            )
            if cache.is_fresh():
                return cache.weather_data
            else:
                cache.delete()
        except WeatherCache.DoesNotExist:
            pass
        
        # Fetch from API
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': cls.API_KEY,
            'units': 'metric'
        }
        
        try:
            response = requests.get(cls.CURRENT_WEATHER_URL, params=params, timeout=5)
            response.raise_for_status()
            weather_data = response.json()
            
            # Cache the result
            WeatherCache.objects.update_or_create(
                latitude=float(latitude),
                longitude=float(longitude),
                defaults={'weather_data': weather_data}
            )
            
            return weather_data
        except Exception as e:
            logger.error(f"Error fetching weather: {str(e)}")
            return None
    
    @classmethod
    def get_weather_forecast(cls, latitude, longitude, days=5):
        """Get weather forecast for upcoming days"""
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': cls.API_KEY,
            'units': 'metric',
            'cnt': min(days * 8, 40)  # 5-day forecast (8 forecasts per day)
        }
        
        try:
            response = requests.get(cls.FORECAST_URL, params=params, timeout=5)
            response.raise_for_status()
            forecast_data = response.json()
            
            # Parse and organize by day
            daily_forecasts = {}
            for item in forecast_data.get('list', []):
                date = item['dt_txt'].split()[0]
                if date not in daily_forecasts:
                    daily_forecasts[date] = {
                        'date': date,
                        'temp_min': item['main']['temp_min'],
                        'temp_max': item['main']['temp_max'],
                        'humidity': item['main']['humidity'],
                        'description': item['weather'][0]['description'],
                        'rainfall_probability': item.get('pop', 0) * 100,
                    }
                else:
                    # Update with min/max
                    daily_forecasts[date]['temp_min'] = min(
                        daily_forecasts[date]['temp_min'], 
                        item['main']['temp_min']
                    )
                    daily_forecasts[date]['temp_max'] = max(
                        daily_forecasts[date]['temp_max'], 
                        item['main']['temp_max']
                    )
            
            return list(daily_forecasts.values())
        except Exception as e:
            logger.error(f"Error fetching forecast: {str(e)}")
            return []
    
    @classmethod
    def get_farming_advisory(cls, weather_data, crop_type='general'):
        """Generate farming advisory based on weather"""
        if not weather_data:
            return None
        
        advisories = {
            'rainy': "Good time for watering. Ensure proper drainage to prevent waterlogging.",
            'clear': "Good for field activities. Monitor soil moisture as evaporation will be high.",
            'cloudy': "Moderate weather. Continue regular farming activities.",
            'hot': "High temperatures. Increase irrigation frequency and watch for pest activity.",
            'cold': "Cold weather detected. Protect sensitive crops and monitor for frost.",
        }
        
        weather = weather_data.get('weather', [{}])[0]
        main_weather = weather.get('main', '').lower()
        temp = weather_data.get('main', {}).get('temp', 0)
        humidity = weather_data.get('main', {}).get('humidity', 0)
        
        # Generate advisory
        advice = advisories.get('cloudy')
        
        if 'rain' in main_weather:
            advice = advisories['rainy']
        elif temp > 35:
            advice = advisories['hot']
        elif temp < 10:
            advice = advisories['cold']
        elif 'clear' in main_weather or 'sunny' in main_weather:
            advice = advisories['clear']
        
        return {
            'current_weather': main_weather,
            'temperature': temp,
            'humidity': humidity,
            'advisory': advice
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
    """Service for fetching weather data from OpenWeatherMap (free tier)"""
    
    API_KEY = getattr(settings, 'OPENWEATHER_API_KEY', '')
    BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
    
    @classmethod
    def get_weather(cls, latitude, longitude):
        """Get weather for location with caching"""
        # Check cache first
        try:
            cache = WeatherCache.objects.get(
                latitude=float(latitude),
                longitude=float(longitude)
            )
            if cache.is_fresh():
                return cache.weather_data
            else:
                cache.delete()
        except WeatherCache.DoesNotExist:
            pass
        
        # Fetch from API
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': cls.API_KEY,
            'units': 'metric'
        }
        
        try:
            response = requests.get(cls.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            weather_data = response.json()
            
            # Cache the result
            WeatherCache.objects.update_or_create(
                latitude=float(latitude),
                longitude=float(longitude),
                defaults={'weather_data': weather_data}
            )
            
            return weather_data
        except Exception as e:
            logger.error(f"Error fetching weather: {str(e)}")
            return None
    
    @classmethod
    def get_farming_advisory(cls, weather_data, crop_type='general'):
        """Generate farming advisory based on weather"""
        if not weather_data:
            return None
        
        advisories = {
            'rainy': "Good time for watering. Ensure proper drainage to prevent waterlogging.",
            'clear': "Good for field activities. Monitor soil moisture as evaporation will be high.",
            'cloudy': "Moderate weather. Continue regular farming activities.",
            'hot': "High temperatures. Increase irrigation frequency and watch for pest activity.",
            'cold': "Cold weather detected. Protect sensitive crops and monitor for frost.",
        }
        
        weather = weather_data.get('weather', [{}])[0]
        main_weather = weather.get('main', '').lower()
        temp = weather_data.get('main', {}).get('temp', 0)
        humidity = weather_data.get('main', {}).get('humidity', 0)
        
        # Generate advisory
        advice = advisories.get('cloudy')
        
        if 'rain' in main_weather:
            advice = advisories['rainy']
        elif temp > 35:
            advice = advisories['hot']
        elif temp < 10:
            advice = advisories['cold']
        elif 'clear' in main_weather or 'sunny' in main_weather:
            advice = advisories['clear']
        
        return {
            'current_weather': main_weather,
            'temperature': temp,
            'humidity': humidity,
            'advisory': advice
        }


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
