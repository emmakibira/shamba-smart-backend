from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.users.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'phone_number', 'latitude', 'longitude', 'location_address',
            'farm_size', 'primary_crops', 'soil_type', 'profile_picture', 'bio'
        ]


class RegisterSerializer(serializers.Serializer):
    """Register with Firebase and location data"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    location_address = serializers.CharField(required=False)
    farm_size = serializers.FloatField()
    primary_crops = serializers.ListField(child=serializers.CharField())
    soil_type = serializers.CharField(default='loam')
    
    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Email already registered."})
        
        return data
    
    def create(self, validated_data):
        email = validated_data['email']
        
        # Create Django user (username will be email)
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        user.set_password(validated_data['password'])
        user.save()
        
        # Create profile with location and farm data
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.phone_number = validated_data.get('phone_number', '')
        profile.latitude = validated_data['latitude']
        profile.longitude = validated_data['longitude']
        profile.location_address = validated_data.get('location_address', '')
        profile.farm_size = validated_data['farm_size']
        profile.primary_crops = validated_data['primary_crops']
        profile.soil_type = validated_data.get('soil_type', 'loam')
        profile.save()
        
        return user


class LoginSerializer(serializers.Serializer):
    """Firebase token login"""
    firebase_token = serializers.CharField()
    
    def validate(self, data):
        from utils.firebase_utils import FirebaseAuth
        
        token = data['firebase_token']
        decoded_token = FirebaseAuth.verify_token(token)
        
        if not decoded_token:
            raise serializers.ValidationError("Invalid Firebase token")
        
        self.decoded_token = decoded_token
        return data


class UserLoginResponseSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
