from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.crops.models import Crop, CropRecommendation
from apps.crops.serializers import CropSerializer, CropRecommendationSerializer

class CropViewSet(viewsets.ModelViewSet):
    serializer_class = CropSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Crop.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CropRecommendationViewSet(viewsets.ModelViewSet):
    serializer_class = CropRecommendationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return CropRecommendation.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def all_recommendations(self, request):
        """Get all recommendations for the current user"""
        recommendations = self.get_queryset()
        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)
