from rest_framework import serializers
from django.contrib.auth.models import User
from apps.users.models import UserProfile, FarmData


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user farm profile"""
    class Meta:
        model = UserProfile
        fields = [
            'id', 'phone_number', 'latitude', 'longitude', 'location_address',
            'farm_size', 'primary_crops', 'soil_type', 'years_of_experience',
            'bio', 'profile_picture', 'is_premium', 'premium_expiry',
            'posts_created_this_month', 'created_at', 'updated_at'
        ]
        read_only_fields = ['is_premium', 'premium_expiry', 'posts_created_this_month', 'created_at', 'updated_at']


class FarmDataSerializer(serializers.ModelSerializer):
    """Serializer for historical farm data"""
    class Meta:
        model = FarmData
        fields = [
            'id', 'crop_name', 'planting_date', 'expected_harvest_date',
            'actual_harvest_date', 'area_planted', 'yield_obtained', 'notes', 'created_at'
        ]
        read_only_fields = ['created_at']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        
        if profile_data:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                if attr not in ['id', 'is_premium', 'premium_expiry', 'posts_created_this_month', 'created_at', 'updated_at']:
                    setattr(profile, attr, value)
            profile.save()
        
        return instance
