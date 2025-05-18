from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Game(Base):
    __tablename__ = "games"
    id = Column(String, primary_key=True, index=True)
    state = Column(Text)
    current_player_id = Column(Integer, ForeignKey("users.id"))

class Move(Base):
    __tablename__ = "moves"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("users.id"))
    move_data = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
