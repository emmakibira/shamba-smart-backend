from django.contrib import admin
from .models import Payment, StripeEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'plan', 'status', 'amount', 'created_at']
    list_filter = ['status', 'plan', 'created_at']
    search_fields = ['user_profile__user__email', 'stripe_customer_id']
    readonly_fields = ['stripe_customer_id', 'stripe_subscription_id', 'created_at', 'updated_at']


@admin.register(StripeEvent)
class StripeEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'processed', 'created_at']
    list_filter = ['event_type', 'processed', 'created_at']
    search_fields = ['event_id']
    readonly_fields = ['event_id', 'event_type', 'data', 'created_at']
