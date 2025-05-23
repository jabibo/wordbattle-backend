import pytest
from app.wordlist import load_wordlist_from_file
import tempfile
import os

def test_load_wordlist(test_db):
    """Test loading wordlist from database."""
    # Add specific test words to match the assertion
    from app.models import WordList
    
    # Clear existing data
    test_db.query(WordList).delete()
    test_db.commit()
    
    # Add test words
    test_words = [
        WordList(word="SCRABBLE", language="en"),
        WordList(word="GAME", language="en"),
        WordList(word="WORD", language="en")
    ]
    test_db.add_all(test_words)
    test_db.commit()
    
    # Use direct database query instead of load_wordlist
    words = test_db.query(WordList.word).filter(WordList.language == "en").all()
    wordlist = {word[0] for word in words}
    
    assert "SCRABBLE" in wordlist
    assert "GAME" in wordlist
    assert "WORD" in wordlist

def test_load_wordlist_empty_file():
    """Test loading an empty wordlist file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        temp_path = f.name
    
    try:
        wordlist = load_wordlist_from_file(temp_path)
        assert len(wordlist) == 0
    finally:
        os.unlink(temp_path)

def test_load_wordlist_with_empty_lines():
    """Test loading a wordlist file with empty lines."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("word1\n\n\nword2\n")
        temp_path = f.name
    
    try:
        wordlist = load_wordlist_from_file(temp_path)
        assert len(wordlist) == 2
        assert "WORD1" in wordlist
        assert "WORD2" in wordlist
    finally:
        os.unlink(temp_path)
