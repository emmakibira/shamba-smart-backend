from django.db import models
from apps.users.models import UserProfile


class ChatMessage(models.Model):
    """Store chatbot conversation history"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='chat_messages')
    user_message = models.TextField()
    assistant_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['user_profile', '-created_at']),
        ]
    
    def __str__(self):
        return f"Chat with {self.user_profile.user.email}"


class DiseaseDetection(models.Model):
    """Store disease detection results"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='disease_detections')
    image = models.ImageField(upload_to='disease_images/')
    disease_name = models.CharField(max_length=200)
    confidence = models.FloatField()  # 0.0 to 1.0
    treatment_suggestions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.disease_name} ({self.confidence:.2%})"


class YieldPrediction(models.Model):
    """Store yield predictions"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='yield_predictions')
    crop_name = models.CharField(max_length=100)
    expected_yield_per_hectare = models.FloatField()  # in kg/hectare
    confidence = models.FloatField()  # 0.0 to 1.0
    factors_considered = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.crop_name} - {self.expected_yield_per_hectare:.2f} kg/ha"
