from django.contrib import admin
from apps.crops.models import Crop, CropRecommendation

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ['name', 'crop_type', 'user', 'health_percentage', 'status', 'created_at']
    list_filter = ['status', 'crop_type']
    search_fields = ['name', 'user__username']

@admin.register(CropRecommendation)
class CropRecommendationAdmin(admin.ModelAdmin):
    list_display = ['crop_name', 'user', 'profit_margin', 'season', 'confidence_score']
    list_filter = ['season']
    search_fields = ['crop_name', 'user__username']
