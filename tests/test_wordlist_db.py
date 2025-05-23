import pytest
from sqlalchemy.orm import Session
from app.models import WordList

def test_wordlist_model(test_db: Session):
    """Test the WordList model."""
    # Clear existing data
    test_db.query(WordList).delete()
    test_db.commit()
    
    # Create test words
    words = [
        WordList(id=101, word="APPLE", language="en"),
        WordList(id=102, word="BANANA", language="en"),
        WordList(id=103, word="APFEL", language="de"),
        WordList(id=104, word="BANANE", language="de")
    ]
    
    # Add to database
    test_db.add_all(words)
    test_db.commit()
    
    # Query by language
    en_words = test_db.query(WordList).filter(WordList.language == "en").all()
    de_words = test_db.query(WordList).filter(WordList.language == "de").all()
    
    assert len(en_words) == 2
    assert len(de_words) == 2
    assert en_words[0].word in ["APPLE", "BANANA"]
    assert de_words[0].word in ["APFEL", "BANANE"]
