from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.dashboard.models import WeatherData, AlertNotification
from apps.dashboard.serializers import WeatherDataSerializer, AlertNotificationSerializer
from apps.crops.models import Crop, CropRecommendation
from apps.crops.serializers import CropSerializer, CropRecommendationSerializer

class WeatherViewSet(viewsets.ModelViewSet):
    serializer_class = WeatherDataSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WeatherData.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current weather for user"""
        weather, _ = WeatherData.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(weather)
        return Response(serializer.data)

class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AlertNotification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread alerts"""
        alerts = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all alerts as read"""
        self.get_queryset().update(is_read=True)
        return Response({'status': 'All alerts marked as read'})

class DashboardViewSet(viewsets.ViewSet):
    """Dashboard overview endpoint"""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get dashboard overview with all data"""
        user = request.user
        
        # Weather data
        weather, _ = WeatherData.objects.get_or_create(user=user)
        weather_data = WeatherDataSerializer(weather).data
        
        # User crops
        crops = Crop.objects.filter(user=user)
        crops_data = CropSerializer(crops, many=True).data
        
        # Recommendations
        recommendations = CropRecommendation.objects.filter(user=user)[:3]
        recommendations_data = CropRecommendationSerializer(recommendations, many=True).data
        
        # Alerts (unread count)
        unread_alerts = AlertNotification.objects.filter(user=user, is_read=False).count()
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'weather': weather_data,
            'crops': crops_data,
            'recommendations': recommendations_data,
            'unread_alerts': unread_alerts,
        })
