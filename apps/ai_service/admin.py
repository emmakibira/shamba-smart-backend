from django.contrib import admin
from .models import ChatMessage, DiseaseDetection, YieldPrediction


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user_profile__user__email', 'user_message']
    readonly_fields = ['created_at']


@admin.register(DiseaseDetection)
class DiseaseDetectionAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'disease_name', 'confidence', 'created_at']
    list_filter = ['disease_name', 'confidence', 'created_at']
    search_fields = ['user_profile__user__email', 'disease_name']
    readonly_fields = ['created_at']


@admin.register(YieldPrediction)
class YieldPredictionAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'crop_name', 'expected_yield_per_hectare', 'created_at']
    list_filter = ['crop_name', 'created_at']
    search_fields = ['user_profile__user__email', 'crop_name']
    readonly_fields = ['created_at']
