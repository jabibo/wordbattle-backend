"""Utility for sending push notifications with user preferences and quiet hours."""
from datetime import datetime, time as dt_time
from typing import Optional, List
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def is_within_quiet_hours(quiet_hours_start: Optional[str], quiet_hours_end: Optional[str]) -> bool:
    """Check if current time is within quiet hours."""
    if not quiet_hours_start or not quiet_hours_end:
        return False

    try:
        now = datetime.now().time()
        start = datetime.strptime(quiet_hours_start, "%H:%M").time()
        end = datetime.strptime(quiet_hours_end, "%H:%M").time()

        if start <= end:
            return start <= now <= end
        else:  # Quiet hours span midnight
            return now >= start or now <= end
    except (ValueError, TypeError):
        return False


async def send_notification_to_user(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    body: str,
    game_id: Optional[str] = None,
    data: Optional[dict] = None,
) -> bool:
    """
    Send push notification to user, respecting preferences and quiet hours.
    Returns True if at least one notification was sent.
    """
    from app.models import PushToken, NotificationPreferences, NotificationLog
    from app.services.firebase_service import send_push_notification, is_push_configured

    if not is_push_configured():
        logger.debug("Push notifications not configured - skipping")
        return False

    # Get user's active tokens
    tokens = db.query(PushToken).filter(
        PushToken.user_id == user_id,
        PushToken.is_active == True,
    ).all()

    if not tokens:
        logger.debug(f"No push tokens for user {user_id}")
        return False

    # Get preferences
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == user_id,
    ).first()

    # Check type-specific preference
    type_enabled = True
    if prefs:
        if notification_type == "game_move" and not prefs.game_moves:
            type_enabled = False
        elif notification_type == "invitation" and not prefs.invitations:
            type_enabled = False
        elif notification_type == "game_completion" and not prefs.game_completion:
            type_enabled = False
        elif notification_type == "chat" and not prefs.chat_messages:
            type_enabled = False

        # Check quiet hours
        if prefs.quiet_hours_enabled and is_within_quiet_hours(
            prefs.quiet_hours_start, prefs.quiet_hours_end
        ):
            logger.debug(f"User {user_id} in quiet hours - skipping notification")
            return False

    if not type_enabled:
        logger.debug(f"User {user_id} has disabled {notification_type} notifications")
        return False

    # Build data payload
    payload = data or {}
    if game_id:
        payload["game_id"] = game_id
    payload["type"] = notification_type

    success = False
    for pt in tokens:
        result = False
        error_msg = None
        try:
            result = await send_push_notification(
                token=pt.token,
                title=title,
                body=body,
                data=payload,
            )
            if result:
                success = True
        except Exception as e:
            logger.error(f"Failed to send to token {pt.id}: {e}")
            error_msg = str(e)

        log_entry = NotificationLog(
            user_id=user_id,
            notification_type=notification_type,
            game_id=game_id,
            success=result,
            error_message=error_msg,
        )
        db.add(log_entry)

    db.commit()
    return success
