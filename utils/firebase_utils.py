import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class FirebaseAuth:
    """Firebase authentication utilities"""
    
    _app = None
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase app"""
        if cls._app is not None:
            return
        
        try:
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
            if cred_path:
                cred = credentials.Certificate(cred_path)
                cls._app = firebase_admin.initialize_app(cred)
        except Exception as e:
            logger.warning(f"Firebase initialization warning: {str(e)}")
    
    @classmethod
    def verify_token(cls, token):
        """Verify Firebase ID token"""
        try:
            cls.initialize()
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            logger.error(f"Firebase token verification error: {str(e)}")
            return None
    
    @classmethod
    def get_user_by_uid(cls, uid):
        """Get Firebase user by UID"""
        try:
            cls.initialize()
            user = auth.get_user(uid)
            return user
        except Exception as e:
            logger.error(f"Firebase get user error: {str(e)}")
            return None
