"""Firebase Cloud Messaging service for push notifications."""
import logging
import os
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Lazy initialization - only load firebase_admin when needed
_firebase_initialized = False


def _get_firebase_app():
    """Initialize and return Firebase app. Returns None if not configured."""
    global _firebase_initialized

    if not os.getenv("ENABLE_PUSH_NOTIFICATIONS", "false").lower() == "true":
        logger.debug("Push notifications disabled (ENABLE_PUSH_NOTIFICATIONS=false)")
        return None

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not cred_path or not os.path.exists(cred_path):
        logger.warning("Firebase credentials not found - push notifications disabled")
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials

        # Check if already initialized
        try:
            return firebase_admin.get_app()
        except ValueError:
            pass

        cred = credentials.Certificate(cred_path)
        app = firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin initialized with credentials")
        return app
    except ImportError:
        logger.warning("firebase-admin not installed - push notifications disabled")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin: {e}")
        return None


async def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    badge: Optional[int] = None,
) -> bool:
    """Send push notification to a single device. Returns False if disabled or failed."""
    app = _get_firebase_app()
    if app is None:
        return False

    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=token,
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        badge=badge,
                        sound="default",
                        content_available=True,
                    )
                )
            ),
        )

        response = messaging.send(message)
        logger.info(f"Push notification sent: {response}")
        return True

    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        return False


async def send_push_multicast(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Send notification to multiple devices."""
    app = _get_firebase_app()
    if app is None:
        return {"success_count": 0, "failure_count": len(tokens), "invalid_tokens": tokens}

    try:
        from firebase_admin import messaging

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            tokens=tokens,
        )

        response = messaging.send_multicast(message)
        invalid_tokens = [
            tokens[idx] for idx, resp in enumerate(response.responses) if not resp.success
        ]
        return {
            "success_count": response.success_count,
            "failure_count": response.failure_count,
            "invalid_tokens": invalid_tokens,
        }
    except Exception as e:
        logger.error(f"Failed to send multicast: {e}")
        return {"success_count": 0, "failure_count": len(tokens), "invalid_tokens": tokens}


def is_push_configured() -> bool:
    """Check if push notifications are properly configured."""
    return _get_firebase_app() is not None
