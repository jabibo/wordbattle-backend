from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_id = Column(String, ForeignKey("games.id"))
    rack = Column(String)  # Buchstaben als String z. B. "HALLOTE"
    score = Column(Integer, default=0)

    user = relationship("User")
    game = relationship("Game")
