from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from apps.users.models import UserProfile, FarmData
from apps.users.serializers import (
    UserSerializer, UserDetailSerializer, UserProfileSerializer,
    FarmDataSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'update':
            return UserDetailSerializer
        return UserSerializer

    def get_queryset(self):
        # Users can only see their own profile
        if not self.request.user.is_staff:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()


class ProfileViewSet(viewsets.ViewSet):
    """Get and update current user profile"""
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    def update(self, request):
        user = request.user
        serializer = UserDetailSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FarmDataListCreateView(generics.ListCreateAPIView):
    """List and create farm data records"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FarmDataSerializer
    
    def get_queryset(self):
        return FarmData.objects.filter(user_profile=self.request.user.profile)
    
    def perform_create(self, serializer):
        serializer.save(user_profile=self.request.user.profile)


class FarmDataDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete farm data"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FarmDataSerializer
    
    def get_queryset(self):
        return FarmData.objects.filter(user_profile=self.request.user.profile)
