from rest_framework import serializers
from .models import MarketPrice


class MarketPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketPrice
        fields = ['id', 'crop_name', 'price', 'market', 'date', 'created_at']
