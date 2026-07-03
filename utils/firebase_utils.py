import firebase_admin
from firebase_admin import credentials, auth, firestore
from django.conf import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FirebaseAuth:
    """Firebase authentication utilities"""

    _app = None

    @classmethod
    def initialize(cls):
        """Initialize Firebase app"""
        if cls._app is not None:
            return cls._app

        try:
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
            if cred_path:
                try:
                    cred = credentials.Certificate(cred_path)
                    cls._app = firebase_admin.initialize_app(cred)
                except FileNotFoundError:
                    logger.warning(
                        "Firebase credentials file not found at %s, falling back to default application credentials.",
                        cred_path,
                    )
                    cls._app = firebase_admin.initialize_app()
            else:
                cls._app = firebase_admin.initialize_app()
        except ValueError as e:
            logger.warning(f"Firebase app already initialized: {str(e)}")
            cls._app = firebase_admin.get_app()
        except Exception as e:
            logger.warning(f"Firebase initialization warning: {str(e)}")
        return cls._app

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
    def get_firestore_client(cls):
        cls.initialize()
        try:
            return firestore.client()
        except Exception as e:
            logger.error(f"Could not create Firestore client: {str(e)}")
            return None

    @classmethod
    def get_latest_market_report(cls):
        db = cls.get_firestore_client()
        if not db:
            return None

        try:
            coll = db.collection("marketReports")
            docs = coll.order_by("weekEnd", direction=firestore.Query.DESCENDING).limit(1).stream()
            latest = next(docs, None)
            if latest and latest.exists:
                return latest.to_dict()
        except Exception as e:
            logger.exception(f"Error loading market report from Firestore: {e}")
        return None

    @classmethod
    def get_market_prices(cls, crop: str | None = None, limit: int = 100):
        db = cls.get_firestore_client()
        if not db:
            return None

        try:
            coll = db.collection("marketPrices")
            query = coll.order_by("date", direction=firestore.Query.DESCENDING).limit(limit)
            if crop:
                query = query.where("crop_name", "==", crop)
            return [doc.to_dict() for doc in query.stream()]
        except Exception as e:
            logger.exception(f"Error loading market prices from Firestore: {e}")
        return None

    @classmethod
    def write_market_price_rows(cls, rows, metadata=None):
        db = cls.get_firestore_client()
        if not db:
            return

        try:
            batch = db.batch()
            for row in rows:
                row_id = (
                    f"{row.get('crop_name','')}_{row.get('market','')}_{row.get('date','')}"
                    .lower()
                    .replace(" ", "_")
                    .replace("/", "_")
                    .replace("\\", "_")
                )
                doc_ref = db.collection("marketPrices").document(row_id)
                data = {
                    "crop_name": row.get("crop_name"),
                    "price": row.get("price"),
                    "market": row.get("market"),
                    "date": row.get("date"),
                    "created_at": row.get("created_at") or datetime.utcnow().isoformat(),
                    "uploaded_by": row.get("uploaded_by"),
                }
                if metadata is not None:
                    data["metadata"] = metadata
                batch.set(doc_ref, data, merge=True)
            batch.commit()
        except Exception as e:
            logger.exception(f"Error saving market prices to Firestore: {e}")

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
