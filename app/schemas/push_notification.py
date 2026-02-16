"""Pydantic schemas for push notification API."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PushTokenCreate(BaseModel):
    """Request schema for registering a push token."""
    token: str = Field(..., description="FCM device token")
    platform: str = Field(..., description="Platform: ios or android")
    app_version: Optional[str] = None


class PushTokenResponse(BaseModel):
    """Response schema for push token."""
    id: int
    user_id: int
    platform: str
    app_version: Optional[str] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class NotificationPreferencesUpdate(BaseModel):
    """Request schema for updating notification preferences."""
    game_moves: Optional[bool] = None
    invitations: Optional[bool] = None
    game_completion: Optional[bool] = None
    chat_messages: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    quiet_hours_end: Optional[str] = Field(None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')


class NotificationPreferencesResponse(BaseModel):
    """Response schema for notification preferences."""
    user_id: int
    game_moves: bool
    invitations: bool
    game_completion: bool
    chat_messages: bool
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None

    class Config:
        from_attributes = True
