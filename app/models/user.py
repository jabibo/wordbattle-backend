from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)  # Make nullable for email-only auth
    is_admin = Column(Boolean, default=False)
    is_word_admin = Column(Boolean, default=False)  # Word admin privilege
    
    # User preferences
    language = Column(String, default="en")  # User's preferred language
    
    # Invitation preferences
    allow_invites = Column(Boolean, default=True)  # "No invites" switch
    preferred_languages = Column(JSON, default=lambda: ["en", "de"])  # Languages user wants to receive invites for
    
    # Email verification fields
    verification_code = Column(String, nullable=True)
    verification_code_expires = Column(DateTime, nullable=True)
    is_email_verified = Column(Boolean, default=False)
    
    # Persistent authentication
    persistent_token = Column(String, nullable=True)  # For "remember me" functionality
    persistent_token_expires = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    moves = relationship("Move", back_populates="player")
    games_created = relationship("Game", foreign_keys="[Game.creator_id]", back_populates="creator")
    games_playing = relationship("Game", foreign_keys="[Game.current_player_id]", back_populates="current_player")
    invitations_sent = relationship("GameInvitation", foreign_keys="[GameInvitation.inviter_id]", back_populates="inviter")
    invitations_received = relationship("GameInvitation", foreign_keys="[GameInvitation.invitee_id]", back_populates="invitee")
    sent_messages = relationship("ChatMessage", back_populates="sender")
    
    # Words added by this user as word admin
    words_added = relationship("WordList", back_populates="added_by_user")