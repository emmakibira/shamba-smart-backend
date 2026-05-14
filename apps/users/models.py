from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """Extended user profile for farmers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=255, blank=True)
    farm_size = models.FloatField(help_text="Farm size in hectares", null=True, blank=True)
    years_of_experience = models.IntegerField(default=0)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
