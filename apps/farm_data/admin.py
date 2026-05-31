from django.contrib import admin
from .models import CommodityPrice, Market, WeatherCache


@admin.register(CommodityPrice)
class CommodityPriceAdmin(admin.ModelAdmin):
    list_display = ['commodity_name', 'market_name', 'price_per_unit', 'unit', 'date_recorded']
    list_filter = ['commodity_name', 'market_name', 'date_recorded']
    search_fields = ['commodity_name', 'market_name']
    date_hierarchy = 'date_recorded'


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'phone']
    list_filter = ['city', 'state']
    search_fields = ['name', 'city', 'address']


@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    list_display = ['latitude', 'longitude', 'cached_at']
    readonly_fields = ['cached_at']
