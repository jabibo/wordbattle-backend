from sqlalchemy.orm import Session
from app.models import WordList
from app.wordlist import import_wordlist
from app.config import DEFAULT_WORDLIST_PATH
import os
import codecs
from typing import Set, Optional

def get_wordlist_path(language: str) -> str:
    """Get the appropriate wordlist path based on environment."""
    if os.getenv("TESTING") == "1":
        # Use test wordlist during testing
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(base_dir, "tests", "data", f"{language}_words.txt")
    else:
        # Use production wordlist
        return os.path.join("data", f"{language}_words.txt") if language != "de" else DEFAULT_WORDLIST_PATH

def read_wordlist_file(file_path: str) -> Set[str]:
    """
    Read a wordlist file with proper encoding handling.
    
    Args:
        file_path (str): Path to the wordlist file
    
    Returns:
        Set[str]: Set of words from the file
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        UnicodeError: If the file can't be decoded
    """
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            with codecs.open(file_path, 'r', encoding=encoding) as f:
                return {line.strip().upper() for line in f if line.strip()}
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            raise
    
    raise UnicodeError(f"Could not decode file {file_path} with any of the attempted encodings")

def ensure_wordlist_available(language: str, db: Session) -> bool:
    """
    Ensure the wordlist for the specified language is available in the database.
    If not, import it from the default file.
    
    Args:
        language (str): Language code (e.g., 'de' for German)
        db (Session): Database session
    
    Returns:
        bool: True if wordlist is available for the specified language,
              False if falling back to German
    """
    try:
        # Check if wordlist exists for this language
        count = db.query(WordList).filter(WordList.language == language).count()
        if count == 0:
            # Default to German if language is not specified
            if language == "de":
                print(f"Wordlist for language '{language}' not found. Importing from default path...")
                wordlist_path = get_wordlist_path(language)
                words = read_wordlist_file(wordlist_path)
                
                # Import words to database
                for word in words:
                    word_entry = WordList(word=word, language=language)
                    db.add(word_entry)
                db.commit()
            else:
                # For other languages, check if a file exists
                lang_file = get_wordlist_path(language)
                if os.path.exists(lang_file):
                    print(f"Wordlist for language '{language}' not found. Importing from {lang_file}...")
                    words = read_wordlist_file(lang_file)
                    
                    # Import words to database
                    for word in words:
                        word_entry = WordList(word=word, language=language)
                        db.add(word_entry)
                    db.commit()
                else:
                    # Fall back to German if language file doesn't exist
                    print(f"No wordlist file found for language '{language}'. Falling back to German...")
                    ensure_wordlist_available("de", db)
                    return False
        return True
    except Exception as e:
        db.rollback()
        print(f"Error ensuring wordlist availability: {e}")
        return False

def load_wordlist(language: str, db: Optional[Session] = None) -> Set[str]:
    """
    Load the wordlist for the specified language from the database.
    Returns a set of valid words.
    
    Args:
        language (str): Language code (e.g., 'de' for German)
        db (Session, optional): Database session. If not provided, creates a new session.
    
    Returns:
        Set[str]: Set of valid words for the specified language
    """
    # If no db session provided, create one
    if db is None:
        from app.database import SessionLocal
        db = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        # Try to ensure wordlist is available
        success = ensure_wordlist_available(language, db)
        
        # If not successful, fall back to German
        if not success:
            language = "de"
            ensure_wordlist_available(language, db)
        
        # Query all words for the language
        words = db.query(WordList.word).filter(WordList.language == language).all()
        
        # Convert to set of strings
        return {word[0].upper() for word in words}
    finally:
        if should_close:
            db.close()
