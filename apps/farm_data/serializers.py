from rest_framework import serializers
from .models import CommodityPrice, Market, WeatherCache, SensorDevice, SensorReading, SensorAlert


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


class SensorReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorReading
        fields = ['id', 'value', 'timestamp', 'is_anomaly']
        read_only_fields = ['timestamp']


class SensorAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorAlert
        fields = [
            'id', 'severity', 'message', 'threshold_exceeded',
            'expected_value', 'actual_value', 'is_resolved', 'created_at'
        ]
        read_only_fields = ['created_at']


class SensorDeviceListSerializer(serializers.ModelSerializer):
    latest_reading = serializers.SerializerMethodField()
    active_alerts_count = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = SensorDevice
        fields = [
            'id', 'name', 'sensor_type', 'status', 'location_name',
            'battery_level', 'last_seen', 'unit', 'latest_reading',
            'active_alerts_count', 'is_active'
        ]
        read_only_fields = ['last_seen', 'status']
    
    def get_latest_reading(self, obj):
        """Get most recent reading"""
        reading = obj.readings.latest('timestamp') if obj.readings.exists() else None
        if reading:
            return {
                'value': reading.value,
                'timestamp': reading.timestamp,
                'unit': obj.unit
            }
        return None
    
    def get_active_alerts_count(self, obj):
        """Count unresolved alerts"""
        return obj.alerts.filter(is_resolved=False).count()
    
    def get_is_active(self, obj):
        """Check if sensor is currently active"""
        return obj.is_active()


class SensorDeviceDetailSerializer(serializers.ModelSerializer):
    latest_readings = serializers.SerializerMethodField()
    active_alerts = serializers.SerializerMethodField()
    
    class Meta:
        model = SensorDevice
        fields = [
            'id', 'name', 'device_id', 'sensor_type', 'status', 'location_name',
            'latitude', 'longitude', 'manufacturer', 'model', 'battery_level',
            'firmware_version', 'measurement_interval', 'min_threshold',
            'max_threshold', 'unit', 'last_seen', 'paired_at',
            'latest_readings', 'active_alerts'
        ]
        read_only_fields = ['device_id', 'last_seen', 'paired_at']
    
    def get_latest_readings(self, obj):
        """Get last 24 hours of readings"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(hours=24)
        readings = obj.readings.filter(timestamp__gte=cutoff).order_by('timestamp')
        return SensorReadingSerializer(readings, many=True).data
    
    def get_active_alerts(self, obj):
        """Get unresolved alerts"""
        alerts = obj.alerts.filter(is_resolved=False).order_by('-created_at')[:5]
        return SensorAlertSerializer(alerts, many=True).data


class SensorDeviceCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorDevice
        fields = [
            'name', 'device_id', 'sensor_type', 'location_name',
            'latitude', 'longitude', 'manufacturer', 'model',
            'measurement_interval', 'min_threshold', 'max_threshold', 'unit'
        ]
    
    def create(self, validated_data):
        """Create sensor with user from context"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
