from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User
from utils.firebase_utils import FirebaseAuth
import logging

logger = logging.getLogger(__name__)


class FirebaseAuthentication(TokenAuthentication):
    """Custom authentication backend for Firebase tokens"""
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '').split()
        
        if not auth_header or auth_header[0].lower() != 'bearer' or len(auth_header) != 2:
            return None
        
        token = auth_header[1]
        
        try:
            decoded_token = FirebaseAuth.verify_token(token)
            if not decoded_token:
                raise AuthenticationFailed('Invalid Firebase token')
            
            firebase_uid = decoded_token.get('uid')
            email = decoded_token.get('email')
            
            # Get or create Django user
            user, created = User.objects.get_or_create(
                username=firebase_uid,
                defaults={'email': email}
            )
            
            # Update email if it changed
            if user.email != email:
                user.email = email
                user.save()
            
            # Ensure profile exists
            if not hasattr(user, 'profile'):
                from apps.users.models import UserProfile
                UserProfile.objects.create(user=user, firebase_uid=firebase_uid)
            
            return (user, token)
        
        except Exception as e:
            logger.error(f"Firebase authentication error: {str(e)}")
            raise AuthenticationFailed('Authentication failed')
