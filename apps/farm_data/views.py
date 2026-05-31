from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import CommodityPrice, Market
from .serializers import CommodityPriceSerializer, MarketSerializer
from .services import WeatherService, MarketService


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
