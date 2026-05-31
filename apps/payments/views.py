import stripe
import json
import logging
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import timedelta
from .models import Payment, StripeEvent
from .serializers import PaymentSerializer

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class CreatePaymentIntentView(generics.CreateAPIView):
    """Create a Stripe payment intent for premium subscription"""
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        try:
            user_profile = request.user.profile
            plan = request.data.get('plan', 'monthly')
            
            # Pricing
            prices = {
                'monthly': 999,  # $9.99 in cents
                'annual': 9999,  # $99.99 in cents
            }
            
            amount = prices.get(plan, 999)
            
            # Create or get Stripe customer
            if not user_profile.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=user_profile.user.email,
                    name=user_profile.user.get_full_name() or user_profile.user.username,
                )
                # Save customer ID to profile for later use
            else:
                customer = stripe.Customer.retrieve(user_profile.stripe_customer_id)
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                customer=customer.id,
                description=f"Premium {plan} subscription",
                metadata={
                    'user_id': user_profile.user.id,
                    'plan': plan,
                }
            )
            
            # Create payment record
            payment = Payment.objects.create(
                user_profile=user_profile,
                stripe_customer_id=customer.id,
                stripe_payment_intent_id=payment_intent.id,
                plan=plan,
                amount=amount / 100,  # Convert cents to dollars
                status='pending'
            )
            
            return Response({
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': amount / 100,
                'payment_id': payment.id
            }, status=status.HTTP_201_CREATED)
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionStatusView(generics.RetrieveAPIView):
    """Get user's current subscription status"""
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        user_profile = request.user.profile
        
        return Response({
            'is_premium': user_profile.is_premium,
            'is_premium_active': user_profile.is_premium_active(),
            'premium_plan': user_profile.premium_plan,
            'premium_expiry': user_profile.premium_expiry,
            'posts_created_this_month': user_profile.posts_created_this_month,
            'can_create_post': user_profile.can_create_post(),
        })


class CancelSubscriptionView(generics.GenericAPIView):
    """Cancel user's premium subscription"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            user_profile = request.user.profile
            
            if not user_profile.stripe_subscription_id:
                return Response(
                    {'error': 'No active subscription to cancel'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Cancel subscription with Stripe
            stripe.Subscription.modify(
                user_profile.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            # Update user profile
            user_profile.is_premium = False
            user_profile.premium_expiry = None
            user_profile.stripe_subscription_id = None
            user_profile.save()
            
            return Response({'message': 'Subscription cancelled successfully'})
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Store event
    StripeEvent.objects.create(
        event_id=event['id'],
        event_type=event['type'],
        data=event['data']
    )
    
    # Handle specific events
    if event['type'] == 'payment_intent.succeeded':
        _handle_payment_succeeded(event['data']['object'])
    
    elif event['type'] == 'customer.subscription.created':
        _handle_subscription_created(event['data']['object'])
    
    elif event['type'] == 'customer.subscription.updated':
        _handle_subscription_updated(event['data']['object'])
    
    elif event['type'] == 'customer.subscription.deleted':
        _handle_subscription_deleted(event['data']['object'])
    
    return JsonResponse({'success': True})


def _handle_payment_succeeded(payment_intent):
    """Handle successful payment"""
    try:
        user_id = payment_intent['metadata'].get('user_id')
        plan = payment_intent['metadata'].get('plan')
        
        Payment.objects.filter(
            stripe_payment_intent_id=payment_intent['id']
        ).update(status='completed')
        
    except Exception as e:
        logger.error(f"Error handling payment succeeded: {str(e)}")


def _handle_subscription_created(subscription):
    """Handle subscription creation"""
    try:
        customer_id = subscription['customer']
        subscription_id = subscription['id']
        
        # Find user by Stripe customer ID
        from apps.users.models import UserProfile
        user_profile = UserProfile.objects.get(stripe_customer_id=customer_id)
        
        # Update user profile
        user_profile.is_premium = True
        user_profile.stripe_subscription_id = subscription_id
        user_profile.premium_plan = subscription['metadata'].get('plan', 'monthly')
        
        # Set expiry date
        current_period_end = timezone.datetime.fromtimestamp(
            subscription['current_period_end'],
            tz=timezone.utc
        )
        user_profile.premium_expiry = current_period_end
        user_profile.save()
        
    except Exception as e:
        logger.error(f"Error handling subscription created: {str(e)}")


def _handle_subscription_updated(subscription):
    """Handle subscription update"""
    _handle_subscription_created(subscription)


def _handle_subscription_deleted(subscription):
    """Handle subscription deletion"""
    try:
        customer_id = subscription['customer']
        
        from apps.users.models import UserProfile
        user_profile = UserProfile.objects.get(stripe_customer_id=customer_id)
        
        user_profile.is_premium = False
        user_profile.premium_expiry = None
        user_profile.stripe_subscription_id = None
        user_profile.save()
        
    except Exception as e:
        logger.error(f"Error handling subscription deleted: {str(e)}")
