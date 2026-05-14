from rest_framework import serializers
from apps.crops.models import Crop, CropRecommendation

class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = [
            'id', 'name', 'crop_type', 'area_planted', 'health_percentage',
            'planting_date', 'expected_harvest_date', 'status', 'image', 'notes'
        ]

class CropRecommendationSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    bgColor = serializers.SerializerMethodField()

    class Meta:
        model = CropRecommendation
        fields = [
            'id', 'crop_name', 'profit_margin', 'season', 'description',
            'confidence_score', 'icon', 'color', 'bgColor'
        ]

    def get_icon(self, obj):
        # Return icon name for frontend
        crop_icons = {
            'rice': 'sprout',
            'wheat': 'leaf',
            'corn': 'zap',
        }
        return crop_icons.get(obj.crop_name.lower(), 'sprout')

    def get_color(self, obj):
        crop_colors = {
            'rice': '#2E7D32',
            'wheat': '#8D6E63',
            'corn': '#F57C00',
        }
        return crop_colors.get(obj.crop_name.lower(), '#2E7D32')

    def get_bgColor(self, obj):
        crop_bg = {
            'rice': '#C8E6C9',
            'wheat': '#D7CCC8',
            'corn': '#FFE0B2',
        }
        return crop_bg.get(obj.crop_name.lower(), '#C8E6C9')
