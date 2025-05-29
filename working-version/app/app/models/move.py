from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Move(Base):
    __tablename__ = "moves"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("users.id"))
    move_data = Column(String)
    timestamp = Column(DateTime(timezone=True))
    
    # Relationships
    game = relationship("Game", back_populates="moves")
    player = relationship("User", back_populates="moves")
