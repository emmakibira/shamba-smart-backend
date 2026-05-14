from django.db import models
from django.contrib.auth.models import User

class WeatherData(models.Model):
    """Weather data for user's location"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='weather')
    temperature = models.IntegerField(default=28)
    humidity = models.IntegerField(default=65)
    wind_speed = models.IntegerField(default=12)
    rainfall = models.FloatField(default=15.0)
    condition = models.CharField(max_length=100, default="Partly Cloudy")
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Weather - {self.user.username}"

class AlertNotification(models.Model):
    """Alert notifications for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=50, choices=[
        ('weather', 'Weather'),
        ('disease', 'Disease'),
        ('pest', 'Pest'),
        ('water', 'Water'),
        ('market', 'Market'),
    ])
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"
