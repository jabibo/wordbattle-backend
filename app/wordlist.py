from typing import Set
from app.config import DEFAULT_WORDLIST_PATH
from app.database import SessionLocal
import os

def load_wordlist_from_file(path=None) -> set[str]:
    """
    Load a wordlist from a file.
    
    Args:
        path: Path to the wordlist file. If None, uses the default path from config.
        
    Returns:
        A set of uppercase words from the file.
    """
    if path is None:
        path = DEFAULT_WORDLIST_PATH
    
    # Try different encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(path, encoding=encoding) as f:
                return set(line.strip().upper() for line in f if line.strip())
        except UnicodeDecodeError:
            continue
    
    # If all encodings fail, try binary mode and decode with errors='ignore'
    with open(path, 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')
        return set(line.strip().upper() for line in content.splitlines() if line.strip())

def load_wordlist(language="de") -> set[str]:
    """
    Load a wordlist from the database. Falls back to file if database is empty.
    
    Args:
        language: Language code (e.g., "de", "en")
        
    Returns:
        A set of uppercase words.
    """
    # Only use file-based wordlist in tests if explicitly requested
    if os.environ.get("WORDLIST_TEST_MODE") == "1":
        return load_wordlist_from_file()
    
    # Import here to avoid circular imports
    from app.models.wordlist import WordList
    
    db = SessionLocal()
    try:
        # Check if words exist in the database for this language
        count = db.query(WordList).filter(WordList.language == language).count()
        
        if count > 0:
            # Get words from database
            words = db.query(WordList.word).filter(WordList.language == language).all()
            return {word[0] for word in words}
        else:
            # Fall back to file-based wordlist
            return load_wordlist_from_file()
    finally:
        db.close()

def import_wordlist(language="de", path=None):
    """
    Import a wordlist from a file into the database.
    
    Args:
        language: Language code (e.g., "de", "en")
        path: Path to the wordlist file. If None, uses the default path from config.
    """
    if path is None:
        path = DEFAULT_WORDLIST_PATH
    
    # Load words from file
    words = load_wordlist_from_file(path)
    
    # Import to database
    from app.models.wordlist import WordList
    
    db = SessionLocal()
    try:
        # Check if words already exist for this language
        existing_count = db.query(WordList).filter(WordList.language == language).count()
        if existing_count > 0:
            print(f"Words for language '{language}' already exist in the database. Skipping import.")
            return
        
        # Batch insert for better performance
        batch_size = 1000
        word_list = list(words)
        total_words = len(word_list)
        
        for i in range(0, total_words, batch_size):
            batch = [WordList(word=word, language=language) for word in word_list[i:i+batch_size]]
            db.add_all(batch)
            db.commit()
            print(f"Imported {min(i+batch_size, total_words)}/{total_words} words")
        
        print(f"Successfully imported {total_words} words for language '{language}'")
    finally:
        db.close()

if __name__ == "__main__":
    # When run as a script, import wordlists
    import sys
    
    if len(sys.argv) > 1:
        language = sys.argv[1]
    else:
        language = "de"
    
    if len(sys.argv) > 2:
        path = sys.argv[2]
    else:
        path = DEFAULT_WORDLIST_PATH
    
    print(f"Importing wordlist for language '{language}' from {path}")
    import_wordlist(language, path)
