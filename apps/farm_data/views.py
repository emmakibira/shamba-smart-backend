from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import CommodityPrice, Market, SensorDevice, SensorReading, SensorAlert
from .serializers import (
    CommodityPriceSerializer, MarketSerializer, SensorDeviceListSerializer,
    SensorDeviceDetailSerializer, SensorDeviceCreateUpdateSerializer,
    SensorReadingSerializer, SensorAlertSerializer
)
from .services import WeatherService, MarketService, SensorService


class CommodityPriceListView(generics.ListAPIView):
    """Get latest commodity prices"""
    permission_classes = [AllowAny]
    queryset = CommodityPrice.objects.all()
    serializer_class = CommodityPriceSerializer
    filterset_fields = ['commodity_name', 'market_name']
    ordering = ['-date_recorded']
    
    def get_queryset(self):
        # Get latest prices for each commodity
        queryset = super().get_queryset()
        commodity = self.request.query_params.get('commodity_name')
        if commodity:
            queryset = queryset.filter(commodity_name=commodity)
        return queryset[:20]  # Limit to 20 recent prices


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weather_advisory(request):
    """Get weather and farming advisory for user's farm location"""
    try:
        user_profile = request.user.profile
        
        if not user_profile.latitude or not user_profile.longitude:
            return Response(
                {'error': 'Location not set in profile'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        weather_data = WeatherService.get_weather(
            user_profile.latitude,
            user_profile.longitude
        )
        
        if not weather_data:
            return Response(
                {'error': 'Could not fetch weather data'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        advisory = WeatherService.get_farming_advisory(
            weather_data,
            crop_type=user_profile.primary_crops[0] if user_profile.primary_crops else 'general'
        )
        
        return Response(advisory)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearby_markets(request):
    """Get markets nearby user's farm location"""
    try:
        user_profile = request.user.profile
        
        if not user_profile.latitude or not user_profile.longitude:
            return Response(
                {'error': 'Location not set in profile'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        radius = request.query_params.get('radius', 50)
        
        markets = MarketService.find_nearby_markets(
            user_profile.latitude,
            user_profile.longitude,
            radius_km=float(radius)
        )
        
        market_objects = [m['market'] for m in markets]
        serializer = MarketSerializer(
            market_objects,
            many=True,
            context={
                'user_latitude': user_profile.latitude,
                'user_longitude': user_profile.longitude
            }
        )
        
        return Response({
            'count': len(markets),
            'markets': serializer.data
        })
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crop_recommendations(request):
    """Get AI crop recommendations based on location and soil"""
    try:
        user_profile = request.user.profile
        
        # Get weather for recommendations
        if user_profile.latitude and user_profile.longitude:
            weather = WeatherService.get_weather(
                user_profile.latitude,
                user_profile.longitude
            )
        else:
            weather = None
        
        temp = weather.get('main', {}).get('temp', 20) if weather else 20
        rainfall_data = weather.get('clouds', {}).get('all', 50) if weather else 50
        
        # Simple rule-based recommendations
        recommendations = {
            'loam': ['wheat', 'rice', 'maize', 'pulses', 'vegetables'],
            'clay': ['rice', 'pulses', 'sugarcane'],
            'sandy': ['groundnut', 'millets', 'watermelon', 'vegetables'],
            'silt': ['wheat', 'rice', 'vegetables'],
            'peaty': ['rice', 'vegetables', 'fruits'],
            'chalky': ['pulses', 'vegetables', 'fruit trees'],
        }
        
        soil_recommendations = recommendations.get(user_profile.soil_type, [])
        
        # Adjust by temperature
        if temp > 35:
            temp_suitable = ['millets', 'groundnut', 'watermelon']
        elif temp < 15:
            temp_suitable = ['wheat', 'mustard', 'potato']
        else:
            temp_suitable = ['rice', 'vegetables', 'pulses']
        
        # Final recommendations
        final_recs = list(set(soil_recommendations) & set(temp_suitable))
        
        return Response({
            'soil_type': user_profile.soil_type,
            'temperature': temp,
            'humidity': rainfall_data,
            'recommended_crops': final_recs or soil_recommendations,
            'reason': f"Based on {user_profile.soil_type} soil and current weather conditions"
        })
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


# ============ SENSOR ENDPOINTS ============

class SensorDeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sensor devices.
    List, create, update, delete sensor devices.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only return sensors belonging to the current user"""
        queryset = SensorDevice.objects.filter(user=self.request.user)
        if queryset.count() == 0:
            # Create three mock sensors for the user
            s1 = SensorDevice.objects.create(
                user=self.request.user,
                name="North Field Moisture",
                device_id=f"SM-{self.request.user.id}-1",
                sensor_type="soil_moisture",
                status="active",
                location_name="North Field",
                battery_level=85,
                unit="%",
                min_threshold=30.0,
                max_threshold=80.0
            )
            s2 = SensorDevice.objects.create(
                user=self.request.user,
                name="Greenhouse Temp",
                device_id=f"TM-{self.request.user.id}-2",
                sensor_type="temperature",
                status="active",
                location_name="Greenhouse",
                battery_level=92,
                unit="°C",
                min_threshold=15.0,
                max_threshold=35.0
            )
            s3 = SensorDevice.objects.create(
                user=self.request.user,
                name="South Field pH",
                device_id=f"PH-{self.request.user.id}-3",
                sensor_type="soil_ph",
                status="active",
                location_name="South Field",
                battery_level=78,
                unit="pH",
                min_threshold=5.5,
                max_threshold=7.5
            )
            
            # Add initial readings
            SensorReading.objects.create(sensor=s1, value=42.5)
            SensorReading.objects.create(sensor=s2, value=26.4)
            SensorReading.objects.create(sensor=s3, value=6.2)
            
            queryset = SensorDevice.objects.filter(user=self.request.user)
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail"""
        if self.action == 'retrieve':
            return SensorDeviceDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SensorDeviceCreateUpdateSerializer
        return SensorDeviceListSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new sensor device"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_sensor_reading(request, sensor_id):
    """
    Add a new reading to a sensor.
    Expects: {"value": float}
    """
    try:
        sensor = get_object_or_404(SensorDevice, id=sensor_id, user=request.user)
        
        value = request.data.get('value')
        if value is None:
            return Response(
                {'error': 'Value is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reading = SensorService.add_sensor_reading(sensor.id, float(value))
        
        if reading:
            serializer = SensorReadingSerializer(reading)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': 'Failed to add reading'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sensor_readings(request, sensor_id):
    """
    Get sensor readings for the last N hours.
    Query param: hours (default: 24)
    """
    try:
        sensor = get_object_or_404(SensorDevice, id=sensor_id, user=request.user)
        
        hours = int(request.query_params.get('hours', 24))
        readings = SensorService.get_latest_readings(sensor.id, hours=hours)
        
        if readings is None:
            return Response(
                {'error': 'Sensor not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SensorReadingSerializer(readings, many=True)
        return Response({
            'sensor_id': sensor.id,
            'sensor_name': sensor.name,
            'unit': sensor.unit,
            'readings_count': readings.count(),
            'readings': serializer.data
        })
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sensor_alerts(request, sensor_id):
    """
    Get active alerts for a sensor.
    """
    try:
        sensor = get_object_or_404(SensorDevice, id=sensor_id, user=request.user)
        
        alerts = sensor.alerts.filter(is_resolved=False).order_by('-created_at')
        serializer = SensorAlertSerializer(alerts, many=True)
        
        return Response({
            'sensor_id': sensor.id,
            'sensor_name': sensor.name,
            'active_alerts_count': alerts.count(),
            'alerts': serializer.data
        })
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sensors_summary(request):
    """
    Get summary of all user's sensors and their status.
    """
    try:
        summary = SensorService.get_sensor_summary(request.user)
        return Response(summary)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weather_forecast(request):
    """
    Get weather forecast for next 5 days.
    """
    try:
        user_profile = request.user.profile
        
        if not user_profile.latitude or not user_profile.longitude:
            return Response(
                {'error': 'Location not set in profile'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        days = int(request.query_params.get('days', 5))
        forecast = WeatherService.get_weather_forecast(
            user_profile.latitude,
            user_profile.longitude,
            days=days
        )
        
        return Response({
            'location': {
                'latitude': float(user_profile.latitude),
                'longitude': float(user_profile.longitude)
            },
            'forecast_count': len(forecast),
            'forecast': forecast
        })
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def latest_market_report(request):
    """Get the latest market report containing Tanzanian wholesale averages and regional prices (TZS/kg)"""
    report = {
        "id": "2026-05-11",
        "weekLabel": "11 – 15 Mei, 2026",
        "weekStart": "2026-05-11",
        "weekEnd": "2026-05-15",
        "sourcePdf": "Mwenendo wa Bei za Mazao tarehe 11 - 15 Mei, 2026.pdf",
        "uploadedAt": "2026-05-15T00:00:00.000Z",
        "national": [
            {"crop": "mahindi", "priceThisWeek": 800, "priceLastWeek": 800, "changePercent": 0.0},
            {"crop": "mchele", "priceThisWeek": 2300, "priceLastWeek": 2400, "changePercent": -4.2},
            {"crop": "maharage", "priceThisWeek": 2100, "priceLastWeek": 2100, "changePercent": 0.0},
            {"crop": "mtama", "priceThisWeek": 1600, "priceLastWeek": 1700, "changePercent": -5.9},
            {"crop": "uwele", "priceThisWeek": 1600, "priceLastWeek": 1600, "changePercent": 0.0},
            {"crop": "ulezi", "priceThisWeek": 2100, "priceLastWeek": 2200, "changePercent": -4.5},
            {"crop": "viazi_mviringo", "priceThisWeek": 900, "priceLastWeek": 900, "changePercent": 0.0}
        ],
        "regional": [
            {
                "regionId": "dodoma",
                "regionNameSw": "Dodoma",
                "regionNameEn": "Dodoma",
                "prices": [
                    {"crop": "mahindi", "priceThisWeek": 700, "priceLastWeek": 700, "changePercent": 0.0},
                    {"crop": "mchele", "priceThisWeek": 2900, "priceLastWeek": 3000, "changePercent": -3.3},
                    {"crop": "maharage", "priceThisWeek": 2000, "priceLastWeek": 2100, "changePercent": -4.8},
                    {"crop": "mtama", "priceThisWeek": 1400, "priceLastWeek": 1400, "changePercent": 0.0},
                    {"crop": "uwele", "priceThisWeek": 2100, "priceLastWeek": 2100, "changePercent": 0.0},
                    {"crop": "ulezi", "priceThisWeek": None, "priceLastWeek": None, "changePercent": None},
                    {"crop": "viazi_mviringo", "priceThisWeek": 700, "priceLastWeek": 700, "changePercent": 0.0}
                ]
            },
            {
                "regionId": "arusha",
                "regionNameSw": "Arusha",
                "regionNameEn": "Arusha",
                "prices": [
                    {"crop": "mahindi", "priceThisWeek": 800, "priceLastWeek": 800, "changePercent": 0.0},
                    {"crop": "mchele", "priceThisWeek": 2900, "priceLastWeek": 2900, "changePercent": 0.0},
                    {"crop": "maharage", "priceThisWeek": 2100, "priceLastWeek": 2100, "changePercent": 0.0},
                    {"crop": "mtama", "priceThisWeek": 1300, "priceLastWeek": 1300, "changePercent": 0.0},
                    {"crop": "uwele", "priceThisWeek": 2300, "priceLastWeek": 2300, "changePercent": 0.0},
                    {"crop": "ulezi", "priceThisWeek": 900, "priceLastWeek": 1000, "changePercent": -10.0},
                    {"crop": "viazi_mviringo", "priceThisWeek": None, "priceLastWeek": None, "changePercent": None}
                ]
            },
            {
                "regionId": "dar_es_salaam",
                "regionNameSw": "Dar es Salaam",
                "regionNameEn": "Dar es Salaam",
                "prices": [
                    {"crop": "mahindi", "priceThisWeek": 900, "priceLastWeek": 1100, "changePercent": -18.2},
                    {"crop": "mchele", "priceThisWeek": 2900, "priceLastWeek": 3200, "changePercent": -9.4},
                    {"crop": "maharage", "priceThisWeek": 2800, "priceLastWeek": 2900, "changePercent": -3.4},
                    {"crop": "mtama", "priceThisWeek": 1300, "priceLastWeek": None, "changePercent": None},
                    {"crop": "uwele", "priceThisWeek": 1300, "priceLastWeek": None, "changePercent": None},
                    {"crop": "ulezi", "priceThisWeek": 2300, "priceLastWeek": None, "changePercent": None},
                    {"crop": "viazi_mviringo", "priceThisWeek": None, "priceLastWeek": 700, "changePercent": None}
                ]
            },
            {
                "regionId": "lindi",
                "regionNameSw": "Lindi",
                "regionNameEn": "Lindi",
                "prices": [
                    {"crop": "mahindi", "priceThisWeek": 800, "priceLastWeek": 900, "changePercent": -11.1},
                    {"crop": "mchele", "priceThisWeek": 2700, "priceLastWeek": 2700, "changePercent": 0.0},
                    {"crop": "maharage", "priceThisWeek": 2400, "priceLastWeek": 2500, "changePercent": -4.0},
                    {"crop": "mtama", "priceThisWeek": 2300, "priceLastWeek": 2300, "changePercent": 0.0},
                    {"crop": "uwele", "priceThisWeek": 1800, "priceLastWeek": 3300, "changePercent": None},
                    {"crop": "ulezi", "priceThisWeek": 3300, "priceLastWeek": 800, "changePercent": None},
                    {"crop": "viazi_mviringo", "priceThisWeek": 800, "priceLastWeek": 800, "changePercent": 0.0}
                ]
            },
            {
                "regionId": "morogoro",
                "regionNameSw": "Morogoro",
                "regionNameEn": "Morogoro",
                "prices": [
                    {"crop": "mahindi", "priceThisWeek": 900, "priceLastWeek": 1100, "changePercent": -18.2},
                    {"crop": "mchele", "priceThisWeek": 2900, "priceLastWeek": 2500, "changePercent": 16.0},
                    {"crop": "maharage", "priceThisWeek": 2300, "priceLastWeek": 2700, "changePercent": -14.8},
                    {"crop": "mtama", "priceThisWeek": 1700, "priceLastWeek": 2600, "changePercent": -32.0},
                    {"crop": "uwele", "priceThisWeek": None, "priceLastWeek": 2500, "changePercent": -22.2},
                    {"crop": "ulezi", "priceThisWeek": None, "priceLastWeek": 900, "changePercent": None},
                    {"crop": "viazi_mviringo", "priceThisWeek": 700, "priceLastWeek": None, "changePercent": None}
                ]
            }
        ]
    }
    return Response(report)

