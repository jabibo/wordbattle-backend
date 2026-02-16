"""Push notification token registration and preferences API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.models import User, PushToken, NotificationPreferences
from app.db import get_db
from app.schemas.push_notification import (
    PushTokenCreate,
    PushTokenResponse,
    NotificationPreferencesUpdate,
    NotificationPreferencesResponse,
)
from app.services.firebase_service import is_push_configured

router = APIRouter(prefix="/push", tags=["push_notifications"])


@router.post("/token", response_model=PushTokenResponse)
def register_push_token(
    request: PushTokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register or update FCM device token for push notifications."""
    # Remove token from other users (device switched accounts)
    db.query(PushToken).filter(
        PushToken.token == request.token,
        PushToken.user_id != current_user.id,
    ).delete()

    # Upsert: update if exists for this user, else create
    token_obj = db.query(PushToken).filter(
        PushToken.user_id == current_user.id,
        PushToken.token == request.token,
    ).first()

    if token_obj:
        token_obj.platform = request.platform
        token_obj.app_version = request.app_version
        token_obj.is_active = True
        db.commit()
        db.refresh(token_obj)
        return token_obj

    token_obj = PushToken(
        user_id=current_user.id,
        token=request.token,
        platform=request.platform,
        app_version=request.app_version,
    )
    db.add(token_obj)
    db.commit()
    db.refresh(token_obj)
    return token_obj


@router.delete("/token/{token_id}")
def delete_push_token_by_id(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a push token by ID."""
    token_obj = db.query(PushToken).filter(
        PushToken.id == token_id,
        PushToken.user_id == current_user.id,
    ).first()
    if not token_obj:
        raise HTTPException(status_code=404, detail="Token not found")
    db.delete(token_obj)
    db.commit()
    return {"message": "Token removed"}


@router.delete("/token")
def delete_push_token(
    token: str = Query(..., description="FCM token to remove"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove push token by token string (e.g. on logout)."""
    token_obj = db.query(PushToken).filter(
        PushToken.token == token,
        PushToken.user_id == current_user.id,
    ).first()
    if not token_obj:
        return {"message": "Token not found or already removed"}
    db.delete(token_obj)
    db.commit()
    return {"message": "Token removed"}


@router.get("/preferences", response_model=NotificationPreferencesResponse)
def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's notification preferences. Creates defaults if not set."""
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id,
    ).first()

    if not prefs:
        prefs = NotificationPreferences(
            user_id=current_user.id,
            game_moves=True,
            invitations=True,
            game_completion=True,
            chat_messages=True,
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    return prefs


@router.put("/preferences", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    request: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences."""
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id,
    ).first()

    if not prefs:
        prefs = NotificationPreferences(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prefs, key, value)

    db.commit()
    db.refresh(prefs)
    return prefs


@router.get("/status")
def push_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if push notifications are configured and user has tokens."""
    token_count = db.query(PushToken).filter(
        PushToken.user_id == current_user.id,
        PushToken.is_active == True,
    ).count()
    return {
        "enabled": is_push_configured(),
        "token_count": token_count,
    }
