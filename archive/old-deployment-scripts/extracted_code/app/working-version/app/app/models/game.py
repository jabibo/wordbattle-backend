from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone
import enum

class GameStatus(enum.Enum):
    SETUP = "setup"        # Game is being set up, waiting for invitations
    READY = "ready"        # All players accepted, waiting to start
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Game(Base):
    __tablename__ = "games"
    
    id = Column(String, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_player_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    state = Column(String)  # JSON string containing game state
    status = Column(SQLEnum(GameStatus), default=GameStatus.SETUP)
    language = Column(String, default="de")
    max_players = Column(Integer, default=2)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[creator_id])
    current_player = relationship("User", foreign_keys=[current_player_id])
    players = relationship("Player", back_populates="game")
    invitations = relationship("GameInvitation", back_populates="game")
    moves = relationship("Move", back_populates="game")
    chat_messages = relationship("ChatMessage", back_populates="game")
