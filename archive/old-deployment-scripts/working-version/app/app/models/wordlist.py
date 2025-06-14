from sqlalchemy import Column, Integer, String, Index
from app.database import Base

class WordList(Base):
    __tablename__ = "wordlists"
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False)
    language = Column(String, nullable=False)
    
    # Create an index for faster lookups
    __table_args__ = (
        Index('idx_word_language', word, language),
    )