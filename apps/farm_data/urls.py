from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CommodityPriceListView,
    weather_advisory,
    nearby_markets,
    crop_recommendations,
    SensorDeviceViewSet,
    add_sensor_reading,
    sensor_readings,
    sensor_alerts,
    sensors_summary,
    weather_forecast
)

router = DefaultRouter()
router.register(r'sensors', SensorDeviceViewSet, basename='sensor-device')

urlpatterns = [
    # Existing endpoints
    path('commodity-prices/', CommodityPriceListView.as_view(), name='commodity-prices'),
    path('weather-advisory/', weather_advisory, name='weather-advisory'),
    path('weather-forecast/', weather_forecast, name='weather-forecast'),
    path('nearby-markets/', nearby_markets, name='nearby-markets'),
    path('crop-recommendations/', crop_recommendations, name='crop-recommendations'),
    
    # Sensor endpoints
    path('', include(router.urls)),
    path('sensors/<int:sensor_id>/readings/', sensor_readings, name='sensor-readings'),
    path('sensors/<int:sensor_id>/readings/add/', add_sensor_reading, name='add-sensor-reading'),
    path('sensors/<int:sensor_id>/alerts/', sensor_alerts, name='sensor-alerts'),
    path('sensors-summary/', sensors_summary, name='sensors-summary'),
]

