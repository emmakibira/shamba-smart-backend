from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user_profile.user.email', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user_email', 'plan', 'amount', 'status',
            'subscription_start_date', 'subscription_end_date', 'created_at'
        ]
        read_only_fields = ['id', 'user_email', 'status', 'created_at']
