from sqlalchemy import Column, Integer, String, Index, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone

class WordList(Base):
    __tablename__ = "wordlists"
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False)
    language = Column(String, nullable=False)
    
    # New fields for word admin functionality
    added_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    added_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for existing words
    
    # Relationships
    added_by_user = relationship("User", back_populates="words_added")
    
    # Create an index for faster lookups
    __table_args__ = (
        Index('idx_word_language', word, language),
        Index('idx_added_user', added_user_id),
        Index('idx_added_timestamp', added_timestamp),
    )