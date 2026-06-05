from rest_framework import serializers
from backend.apps.dashboard.models import WeatherData, AlertNotification

class WeatherDataSerializer(serializers.ModelSerializer):
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)

    class Meta:
        model = WeatherData
        fields = [
            'temperature', 'humidity', 'wind_speed', 'rainfall',
            'condition', 'condition_display', 'last_updated'
        ]

class AlertNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertNotification
        fields = ['id', 'title', 'message', 'alert_type', 'is_read', 'created_at']
