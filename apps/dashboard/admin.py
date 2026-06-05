from django.contrib import admin
from backend.apps.dashboard.models import WeatherData, AlertNotification

@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['user', 'temperature', 'humidity', 'condition', 'last_updated']
    search_fields = ['user__username']

@admin.register(AlertNotification)
class AlertNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'alert_type', 'is_read', 'created_at']
    list_filter = ['alert_type', 'is_read']
    search_fields = ['title', 'user__username']
