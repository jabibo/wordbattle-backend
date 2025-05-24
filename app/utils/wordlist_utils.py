from sqlalchemy.orm import Session
from app.models import WordList
from app.wordlist import import_wordlist
from app.config import DEFAULT_WORDLIST_PATH
import os

def ensure_wordlist_available(language: str, db: Session):
    """
    Ensure the wordlist for the specified language is available in the database.
    If not, import it from the default file.
    """
    # Check if wordlist exists for this language
    count = db.query(WordList).filter(WordList.language == language).count()
    if count == 0:
        # Default to German if language is not specified
        if language == "de":
            # Import default German wordlist
            print(f"Wordlist for language '{language}' not found. Importing from default path...")
            import_wordlist(language, DEFAULT_WORDLIST_PATH)
        else:
            # For other languages, check if a file exists
            lang_file = f"data/{language}_words.txt"
            if os.path.exists(lang_file):
                print(f"Wordlist for language '{language}' not found. Importing from {lang_file}...")
                import_wordlist(language, lang_file)
            else:
                # Fall back to German if language file doesn't exist
                print(f"No wordlist file found for language '{language}'. Falling back to German...")
                ensure_wordlist_available("de", db)
                return False
    return True
