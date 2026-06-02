from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


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


class SensorDevice(models.Model):
    """Store paired Bluetooth/IoT sensor devices"""
    SENSOR_TYPES = [
        ('temperature', 'Temperature Sensor'),
        ('humidity', 'Humidity Sensor'),
        ('soil_moisture', 'Soil Moisture Sensor'),
        ('soil_ph', 'Soil pH Sensor'),
        ('soil_nitrogen', 'Soil Nitrogen Sensor'),
        ('light', 'Light Intensity Sensor'),
        ('rain', 'Rain Gauge Sensor'),
        ('wind', 'Wind Speed Sensor'),
        ('multi', 'Multi-parameter Sensor'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sensor_devices')
    name = models.CharField(max_length=255)  # User-defined name
    device_id = models.CharField(max_length=100, unique=True)  # MAC address or UUID
    sensor_type = models.CharField(max_length=50, choices=SENSOR_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    
    # Location on farm
    location_name = models.CharField(max_length=255, blank=True)  # e.g., "North Field"
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Device info
    manufacturer = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=255, blank=True)
    battery_level = models.PositiveIntegerField(default=100, help_text="Battery percentage")
    firmware_version = models.CharField(max_length=50, blank=True)
    
    # Configuration
    measurement_interval = models.PositiveIntegerField(default=300, help_text="Seconds between measurements")
    min_threshold = models.FloatField(null=True, blank=True)  # Alert if below
    max_threshold = models.FloatField(null=True, blank=True)  # Alert if above
    unit = models.CharField(max_length=50, blank=True)  # °C, %, ppm, etc.
    
    # Connectivity
    last_seen = models.DateTimeField(auto_now=True)
    paired_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['device_id']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.sensor_type}) - {self.status}"
    
    def is_active(self):
        """Check if sensor is currently connected"""
        from django.utils import timezone
        from datetime import timedelta
        # Sensor is considered active if heard from in last 10 minutes
        return self.status == 'active' and (timezone.now() - self.last_seen < timedelta(minutes=10))


class SensorReading(models.Model):
    """Store real-time sensor readings"""
    sensor = models.ForeignKey(SensorDevice, on_delete=models.CASCADE, related_name='readings')
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_anomaly = models.BooleanField(default=False)  # Flagged as unusual
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['sensor', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.sensor.name}: {self.value} {self.sensor.unit} @ {self.timestamp}"


class SensorAlert(models.Model):
    """Alerts triggered by sensor thresholds"""
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    sensor = models.ForeignKey(SensorDevice, on_delete=models.CASCADE, related_name='alerts')
    reading = models.ForeignKey(SensorReading, on_delete=models.SET_NULL, null=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    message = models.TextField()
    threshold_exceeded = models.CharField(max_length=50)  # 'min' or 'max'
    expected_value = models.FloatField(null=True)
    actual_value = models.FloatField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sensor', 'is_resolved']),
        ]
    
    def __str__(self):
        return f"{self.sensor.name} - {self.severity}: {self.message}"
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
