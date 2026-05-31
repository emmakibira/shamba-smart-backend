import requests
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import WeatherCache

logger = logging.getLogger(__name__)


class WeatherService:
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
