from django.db import models
from backend.apps.users.models import UserProfile


class Payment(models.Model):
    """Track Stripe payments for premium subscriptions"""
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PLAN_CHOICES = [
        ('monthly', 'Monthly - $9.99'),
        ('annual', 'Annual - $99.99'),
    ]
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='payments')
    stripe_customer_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='monthly')
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # in USD
    currency = models.CharField(max_length=3, default='USD')
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_profile.user.email} - {self.plan}"


class StripeEvent(models.Model):
    """Store Stripe webhook events for logging"""
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=255)
    data = models.JSONField()
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at}"
