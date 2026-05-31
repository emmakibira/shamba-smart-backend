from django.db import models


class CommodityPrice(models.Model):
    """Store commodity prices from markets"""
    commodity_name = models.CharField(max_length=100)
    market_name = models.CharField(max_length=200)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, default='kg')  # kg, quintal, etc.
    date_recorded = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source = models.CharField(max_length=255, blank=True)
    
    class Meta:
        verbose_name_plural = "Commodity Prices"
        ordering = ['-date_recorded']
        indexes = [
            models.Index(fields=['commodity_name', 'date_recorded']),
        ]
    
    def __str__(self):
        return f"{self.commodity_name} - {self.market_name}"


class Market(models.Model):
    """Store market locations for nearby market search"""
    name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    commodities = models.JSONField(default=list, blank=True)  # ['wheat', 'rice']
    phone = models.CharField(max_length=15, blank=True)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city}"


class WeatherCache(models.Model):
    """Cache weather data to minimize API calls"""
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    weather_data = models.JSONField()
    cached_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Weather Caches"
        unique_together = ('latitude', 'longitude')
    
    def is_fresh(self):
        """Check if cache is still valid (3 hours)"""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() - self.cached_at < timedelta(hours=3)
