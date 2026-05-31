from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json

class UserProfile(models.Model):
    """Extended user profile for farmers with location and farm data"""
    
    SOIL_TYPE_CHOICES = [
        ('loam', 'Loam'),
        ('clay', 'Clay'),
        ('sandy', 'Sandy'),
        ('silt', 'Silt'),
        ('peaty', 'Peaty'),
        ('chalky', 'Chalky'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    firebase_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Location data
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    location_address = models.CharField(max_length=255, blank=True)
    
    # Farm data
    farm_size = models.FloatField(
        help_text="Farm size in hectares", 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.1)]
    )
    primary_crops = models.JSONField(default=list, blank=True)  # ['wheat', 'rice', 'corn']
    soil_type = models.CharField(
        max_length=20, 
        choices=SOIL_TYPE_CHOICES, 
        default='loam'
    )
    
    # Profile
    years_of_experience = models.IntegerField(default=0)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    
    # Subscription/Premium
    is_premium = models.BooleanField(default=False)
    premium_expiry = models.DateTimeField(null=True, blank=True)
    premium_plan = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('annual', 'Annual')],
        null=True,
        blank=True
    )
    
    # Usage tracking
    posts_created_this_month = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "User Profiles"
        indexes = [
            models.Index(fields=['firebase_uid']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.location_address}"
    
    def is_premium_active(self):
        """Check if premium subscription is currently active"""
        from django.utils import timezone
        if self.is_premium and self.premium_expiry:
            return self.premium_expiry > timezone.now()
        return False
    
    def can_create_post(self):
        """Check if user can create a new community post"""
        if self.is_premium_active():
            return True
        # Free users: 5 posts per month
        return self.posts_created_this_month < 5
    
    def get_crops_list(self):
        """Get list of crops as list"""
        if isinstance(self.primary_crops, str):
            return json.loads(self.primary_crops)
        return self.primary_crops or []


class FarmData(models.Model):
    """Store historical farm data for analytics"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='farm_data')
    crop_name = models.CharField(max_length=100)
    planting_date = models.DateField()
    expected_harvest_date = models.DateField(null=True, blank=True)
    actual_harvest_date = models.DateField(null=True, blank=True)
    area_planted = models.FloatField(help_text="Area planted in hectares")
    yield_obtained = models.FloatField(null=True, blank=True, help_text="Yield in kg/hectare")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Farm Data"
        ordering = ['-planting_date']
    
    def __str__(self):
        return f"{self.user_profile.user.email} - {self.crop_name}"
