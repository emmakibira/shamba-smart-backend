from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from apps.auth.serializers import RegisterSerializer, LoginSerializer, UserLoginResponseSerializer
from apps.users.models import UserProfile
from utils.firebase_utils import FirebaseAuth
import logging

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register a new user with location and farm details"""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = UserLoginResponseSerializer(user)
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'User registered successfully',
                'user': response_serializer.data,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login user with Firebase token"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            decoded_token = serializer.decoded_token
            firebase_uid = decoded_token.get('uid')
            email = decoded_token.get('email')
            
            if not email:
                email = f"{firebase_uid}@shambasmart.com"
            
            # Get or create user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                name = decoded_token.get('name', 'Farmer')
                first_name = name.split(' ')[0] if name else 'Farmer'
                last_name = ' '.join(name.split(' ')[1:]) if name else ''
                
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                user.save()
            
            # Update or create profile with Firebase UID
            profile, created = UserProfile.objects.get_or_create(user=user)
            if not profile.firebase_uid:
                profile.firebase_uid = firebase_uid
            
            # Ensure it has basic default values if null so that views don't crash
            if profile.latitude is None:
                profile.latitude = -6.179  # Default Dodoma / Tanzania coordinates
            if profile.longitude is None:
                profile.longitude = 35.748
            if profile.farm_size is None:
                profile.farm_size = 1.0
            if profile.soil_type is None or not profile.soil_type:
                profile.soil_type = 'loam'
            if not profile.primary_crops:
                profile.primary_crops = ['maize']
            profile.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            response_serializer = UserLoginResponseSerializer(user)
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'user': response_serializer.data,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Get current user profile"""
        response_serializer = UserLoginResponseSerializer(request.user)
        return Response(response_serializer.data)
    def logout(self, request):
        """Logout user"""
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
