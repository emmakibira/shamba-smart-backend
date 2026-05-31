from django.urls import path
from .views import (
    CreatePaymentIntentView,
    SubscriptionStatusView,
    CancelSubscriptionView,
    stripe_webhook
)

urlpatterns = [
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('subscription-status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('cancel-subscription/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]
