from django.db import models
from django.contrib.auth.models import User

class Crop(models.Model):
    """User's crop data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crops')
    name = models.CharField(max_length=100)
    crop_type = models.CharField(max_length=100)  # e.g., "Rice", "Wheat", "Corn"
    area_planted = models.FloatField(help_text="Area in hectares")
    health_percentage = models.IntegerField(default=100)  # 0-100
    planting_date = models.DateField()
    expected_harvest_date = models.DateField()
    status = models.CharField(max_length=50, choices=[
        ('planted', 'Planted'),
        ('growing', 'Growing'),
        ('mature', 'Mature'),
        ('harvesting', 'Harvesting'),
        ('harvested', 'Harvested'),
    ], default='planted')
    image = models.ImageField(upload_to='crops/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class CropRecommendation(models.Model):
    """AI-generated crop recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    crop_name = models.CharField(max_length=100)
    profit_margin = models.CharField(max_length=50)  # e.g., "+32%"
    season = models.CharField(max_length=50)  # e.g., "Kharif", "Rabi"
    description = models.TextField()
    confidence_score = models.FloatField(default=0.0)  # 0-1
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.crop_name} - {self.user.username}"
