import os
import tempfile
from app.wordlist import load_wordlist

def test_load_wordlist():
    # Create a temporary wordlist file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
        temp.write("HALLO\nWELT\nSCRABBLE\n")
        temp_path = temp.name
    
    try:
        # Test loading the wordlist
        wordlist = load_wordlist(temp_path)
        
        # Check if words are loaded correctly
        assert "HALLO" in wordlist
        assert "WELT" in wordlist
        assert "SCRABBLE" in wordlist
        
        # Check if the wordlist is case-insensitive
        assert "hallo" not in wordlist  # Should be uppercase
        
        # Check total count
        assert len(wordlist) == 3
    finally:
        # Clean up the temporary file
        os.unlink(temp_path)

def test_load_wordlist_empty_file():
    # Create an empty temporary file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
        temp_path = temp.name
    
    try:
        # Test loading an empty wordlist
        wordlist = load_wordlist(temp_path)
        
        # Check if the result is an empty set
        assert isinstance(wordlist, set)
        assert len(wordlist) == 0
    finally:
        # Clean up the temporary file
        os.unlink(temp_path)

def test_load_wordlist_with_empty_lines():
    # Create a wordlist with empty lines
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
        temp.write("HALLO\n\n\nWELT\n")
        temp_path = temp.name
    
    try:
        # Test loading the wordlist
        wordlist = load_wordlist(temp_path)
        
        # Check if empty lines are skipped
        assert len(wordlist) == 2
        assert "HALLO" in wordlist
        assert "WELT" in wordlist
    finally:
        # Clean up the temporary file
        os.unlink(temp_path)