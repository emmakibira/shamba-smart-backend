from rest_framework import serializers
from .models import ChatMessage, DiseaseDetection, YieldPrediction


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'user_message', 'assistant_message', 'created_at']
        read_only_fields = ['created_at']


class DiseaseDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseDetection
        fields = ['id', 'image', 'disease_name', 'confidence', 'treatment_suggestions', 'created_at']
        read_only_fields = ['created_at']


class YieldPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = YieldPrediction
        fields = ['id', 'crop_name', 'expected_yield_per_hectare', 'confidence', 'factors_considered', 'created_at']
        read_only_fields = ['created_at']
