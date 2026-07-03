from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class MarketPrice(models.Model):
    crop_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    market = models.CharField(max_length=200)
    date = models.DateField()
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'crop_name']

    def __str__(self):
        return f"{self.crop_name} @ {self.market} — {self.date}"
