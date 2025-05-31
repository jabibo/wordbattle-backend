import os
import codecs
from typing import Set, Optional
from sqlalchemy.orm import Session

def get_wordlist_path(language: str) -> str:
    """Get the appropriate wordlist path based on environment."""
    if os.getenv("TESTING") == "1":
        # Use test wordlist during testing
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(base_dir, "tests", "data", f"{language}_words.txt")
    else:
        # Use production wordlist
        from app.config import DEFAULT_WORDLIST_PATH
        if language == "de":
            return DEFAULT_WORDLIST_PATH
        else:
            return os.path.join("data", f"{language}_words.txt")

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

def load_wordlist(language: str, db: Optional[Session] = None) -> Set[str]:
    """
    Load the wordlist for the specified language.
    
    In test mode (TESTING=1), loads directly from test files.
    In production mode, loads from database with fallback to files.
    
    Args:
        language (str): Language code (e.g., 'de' for German, 'en' for English)
        db (Session, optional): Database session. Only used in production mode.
    
    Returns:
        Set[str]: Set of valid words for the specified language
    
    Raises:
        FileNotFoundError: If wordlist file is not found
    """
    # In test mode, always load from files
    if os.getenv("TESTING") == "1":
        file_path = get_wordlist_path(language)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Test wordlist file not found: {file_path}")
        return read_wordlist_file(file_path)
    
    # Production mode: try database first, fallback to file
    if db is None:
        from app.database import SessionLocal
        db = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        # Import here to avoid circular imports
        from app.models import WordList
        
        # Check if words exist in the database for this language
        count = db.query(WordList).filter(WordList.language == language).count()
        
        if count > 0:
            # Get words from database
            words = db.query(WordList.word).filter(WordList.language == language).all()
            return {word[0].upper() for word in words}
        else:
            # Fall back to file-based wordlist
            file_path = get_wordlist_path(language)
            if os.path.exists(file_path):
                return read_wordlist_file(file_path)
            else:
                # If no file for this language, fall back to German
                if language != "de":
                    return load_wordlist("de", db)
                else:
                    raise FileNotFoundError(f"No wordlist available for language: {language}")
    finally:
        if should_close:
            db.close()

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
    # In test mode, wordlists are always loaded from files, so this is not needed
    if os.getenv("TESTING") == "1":
        return True
    
    try:
        # Import here to avoid circular imports
        from app.models import WordList
        
        # Check if wordlist exists for this language
        count = db.query(WordList).filter(WordList.language == language).count()
        if count == 0:
            # Try to import from file
            file_path = get_wordlist_path(language)
            if os.path.exists(file_path):
                print(f"Wordlist for language '{language}' not found. Importing from {file_path}...")
                words = read_wordlist_file(file_path)
                
                # Import words to database
                for word in words:
                    word_entry = WordList(word=word, language=language)
                    db.add(word_entry)
                db.commit()
                return True
            else:
                # Fall back to German if language file doesn't exist
                if language != "de":
                    print(f"No wordlist file found for language '{language}'. Falling back to German...")
                    ensure_wordlist_available("de", db)
                    return False
                else:
                    print(f"No wordlist available for German language")
                    return False
        return True
    except Exception as e:
        db.rollback()
        print(f"Error ensuring wordlist availability: {e}")
        return False
