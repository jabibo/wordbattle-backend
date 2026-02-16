"""Push notification models for FCM token storage and preferences."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PushToken(Base):
    """FCM device token for push notifications."""
    __tablename__ = "push_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(512), unique=True, nullable=False, index=True)
    platform = Column(String(20), nullable=False)  # 'ios' or 'android'
    app_version = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="push_tokens")


class NotificationPreferences(Base):
    """User preferences for push notification types and quiet hours."""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    game_moves = Column(Boolean, default=True)
    invitations = Column(Boolean, default=True)
    game_completion = Column(Boolean, default=True)
    chat_messages = Column(Boolean, default=True)
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5))  # "22:00"
    quiet_hours_end = Column(String(5))    # "08:00"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="notification_preferences", uselist=False)


class NotificationLog(Base):
    """Log of sent notifications for debugging and analytics."""
    __tablename__ = "notification_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)
    game_id = Column(String(36))
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    success = Column(Boolean)
    error_message = Column(Text)

    user = relationship("User")
