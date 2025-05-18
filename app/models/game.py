from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Game(Base):
    __tablename__ = "games"
    id = Column(String, primary_key=True, index=True)
    state = Column(String)
    current_player_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    current_player = relationship("User")
