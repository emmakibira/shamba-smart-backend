from django.urls import path
from .views import (
    CommodityPriceListView,
    weather_advisory,
    nearby_markets,
    crop_recommendations
)

urlpatterns = [
    path('commodity-prices/', CommodityPriceListView.as_view(), name='commodity-prices'),
    path('weather-advisory/', weather_advisory, name='weather-advisory'),
    path('nearby-markets/', nearby_markets, name='nearby-markets'),
    path('crop-recommendations/', crop_recommendations, name='crop-recommendations'),
]
