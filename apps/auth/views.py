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
            
            # Get or create user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # User doesn't exist, return error
                return Response({
                    'success': False,
                    'message': 'User not found. Please register first.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Update Firebase UID if not set
            profile, created = UserProfile.objects.get_or_create(user=user)
            if not profile.firebase_uid:
                profile.firebase_uid = firebase_uid
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
