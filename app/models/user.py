from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    moves = relationship("Move", back_populates="player")
    games_created = relationship("Game", foreign_keys="[Game.creator_id]", back_populates="creator")
    games_playing = relationship("Game", foreign_keys="[Game.current_player_id]", back_populates="current_player")
    invitations_sent = relationship("GameInvitation", foreign_keys="[GameInvitation.inviter_id]", back_populates="inviter")
    invitations_received = relationship("GameInvitation", foreign_keys="[GameInvitation.invitee_id]", back_populates="invitee")
    sent_messages = relationship("ChatMessage", back_populates="sender")