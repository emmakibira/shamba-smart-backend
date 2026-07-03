from django.contrib import admin
from .models import MarketPrice

@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display = ['crop_name', 'price', 'market', 'date', 'uploaded_by']
    list_filter = ['date', 'market']
    search_fields = ['crop_name', 'market']
