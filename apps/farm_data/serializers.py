from rest_framework import serializers
from .models import CommodityPrice, Market, WeatherCache


class CommodityPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommodityPrice
        fields = [
            'id', 'commodity_name', 'market_name', 'price_per_unit',
            'unit', 'date_recorded', 'source'
        ]


class MarketSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()
    
    class Meta:
        model = Market
        fields = [
            'id', 'name', 'latitude', 'longitude', 'address', 'city',
            'state', 'commodities', 'phone', 'opening_time', 'closing_time',
            'distance_km'
        ]
    
    def get_distance_km(self, obj):
        """Calculate distance if user coordinates provided"""
        user_lat = self.context.get('user_latitude')
        user_lon = self.context.get('user_longitude')
        
        if not user_lat or not user_lon:
            return None
        
        from math import radians, cos, sin, asin, sqrt
        
        # Haversine formula
        lon1, lat1, lon2, lat2 = map(radians, [float(user_lon), float(user_lat), float(obj.longitude), float(obj.latitude)])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return round(km, 2)
