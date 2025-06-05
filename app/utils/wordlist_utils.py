import os
import codecs
from typing import Set, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Global dictionary cache - loaded once and reused across all requests
_DICTIONARY_CACHE = {}
_CACHE_INITIALIZED = {}

def get_wordlist_path(language: str) -> str:
    """Get the file path for a wordlist based on language code."""
    # Try both formats: de-words.txt and de_words.txt
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    
    # First try hyphenated format
    path_hyphen = os.path.join(base_dir, f"{language}-words.txt")
    if os.path.exists(path_hyphen):
        return path_hyphen
    
    # Then try underscore format
    path_underscore = os.path.join(base_dir, f"{language}_words.txt")
    if os.path.exists(path_underscore):
        return path_underscore
    
    # Default to hyphenated format for error messages
    return path_hyphen

def read_wordlist_file(file_path: str) -> Set[str]:
    """Read words from a wordlist file with proper encoding handling."""
    encodings = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                words = {line.strip().upper() for line in f if line.strip()}
                logger.info(f"Successfully loaded {len(words)} words from {file_path} using {encoding} encoding")
                return words
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            raise FileNotFoundError(f"Wordlist file not found: {file_path}")
    
    # If all encodings fail, try binary mode with UTF-8 and ignore errors
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
            words = {line.strip().upper() for line in content.splitlines() if line.strip()}
            logger.warning(f"Loaded {len(words)} words from {file_path} using fallback binary mode")
            return words
    except Exception as e:
        raise RuntimeError(f"Failed to load wordlist from {file_path}: {str(e)}")

def load_wordlist(language: str, db: Optional[Session] = None) -> Set[str]:
    """
    Load the wordlist for the specified language with caching for performance.
    
    🚀 PERFORMANCE OPTIMIZED: Uses global cache to avoid database queries on every move!
    
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
    # Check cache first - MAJOR PERFORMANCE BOOST! ⚡
    if language in _DICTIONARY_CACHE:
        logger.debug(f"Dictionary cache HIT for language '{language}' - using cached dictionary with {len(_DICTIONARY_CACHE[language])} words")
        return _DICTIONARY_CACHE[language]
    
    logger.info(f"Dictionary cache MISS for language '{language}' - loading dictionary...")
    
    # In test mode, always load from files
    if os.getenv("TESTING") == "1":
        file_path = get_wordlist_path(language)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Test wordlist file not found: {file_path}")
        words = read_wordlist_file(file_path)
        # Cache the result
        _DICTIONARY_CACHE[language] = words
        _CACHE_INITIALIZED[language] = True
        logger.info(f"Cached dictionary for language '{language}' with {len(words)} words (from file)")
        return words
    
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
            # Get words from database - this is the expensive operation we're caching!
            logger.info(f"Loading {count} words from database for language '{language}'...")
            words = db.query(WordList.word).filter(WordList.language == language).all()
            word_set = {word[0].upper() for word in words}
            
            # Cache the result - subsequent requests will be instant! 🚀
            _DICTIONARY_CACHE[language] = word_set
            _CACHE_INITIALIZED[language] = True
            logger.info(f"Cached dictionary for language '{language}' with {len(word_set)} words (from database)")
            return word_set
        else:
            # Fall back to file-based wordlist
            file_path = get_wordlist_path(language)
            if os.path.exists(file_path):
                words = read_wordlist_file(file_path)
                # Cache the result
                _DICTIONARY_CACHE[language] = words
                _CACHE_INITIALIZED[language] = True
                logger.info(f"Cached dictionary for language '{language}' with {len(words)} words (from file fallback)")
                return words
            else:
                # If no file for this language, fall back to German
                if language != "de":
                    logger.warning(f"No wordlist found for language '{language}', falling back to German")
                    return load_wordlist("de", db)
                else:
                    raise FileNotFoundError(f"No wordlist available for language: {language}")
    finally:
        if should_close:
            db.close()

def clear_dictionary_cache(language: Optional[str] = None) -> None:
    """
    Clear the dictionary cache for a specific language or all languages.
    
    Args:
        language (str, optional): Language to clear. If None, clears all cached dictionaries.
    """
    global _DICTIONARY_CACHE, _CACHE_INITIALIZED
    
    if language:
        if language in _DICTIONARY_CACHE:
            del _DICTIONARY_CACHE[language]
        if language in _CACHE_INITIALIZED:
            del _CACHE_INITIALIZED[language]
        logger.info(f"Cleared dictionary cache for language '{language}'")
    else:
        _DICTIONARY_CACHE.clear()
        _CACHE_INITIALIZED.clear()
        logger.info("Cleared all dictionary caches")

def get_cache_status() -> dict:
    """
    Get the current status of the dictionary cache.
    
    Returns:
        dict: Cache status with languages and word counts
    """
    return {
        "cached_languages": list(_DICTIONARY_CACHE.keys()),
        "cache_sizes": {lang: len(words) for lang, words in _DICTIONARY_CACHE.items()},
        "total_cached_words": sum(len(words) for words in _DICTIONARY_CACHE.values())
    }

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

def clear_wordlist_cache(language: Optional[str] = None) -> None:
    """Clear the wordlist cache for a specific language or all languages.
    
    Args:
        language: If provided, only clear cache for this language. 
                 If None, clear all cached dictionaries.
                 
    This should be called whenever words are added to the database to ensure
    the cache is refreshed with the latest words.
    """
    global _DICTIONARY_CACHE, _CACHE_INITIALIZED
    
    if language:
        language = language.lower()
        if language in _DICTIONARY_CACHE:
            logger.info(f"Clearing wordlist cache for language: {language}")
            del _DICTIONARY_CACHE[language]
            _CACHE_INITIALIZED[language] = False
    else:
        logger.info("Clearing all wordlist caches")
        _DICTIONARY_CACHE.clear()
        _CACHE_INITIALIZED.clear()

def get_cache_stats() -> dict:
    """Get statistics about the current cache state."""
    return {
        "cached_languages": list(_DICTIONARY_CACHE.keys()),
        "cache_sizes": {lang: len(words) for lang, words in _DICTIONARY_CACHE.items()},
        "total_cached_words": sum(len(words) for words in _DICTIONARY_CACHE.values())
    }

def load_wordlist(language: str) -> Set[str]:
    """Load a wordlist with intelligent caching.
    
    First checks cache, then tries database, falls back to file.
    Cache is automatically invalidated when words are added via word admin.
    """
    language = language.lower()
    
    # Check if already cached and valid
    if language in _DICTIONARY_CACHE and _CACHE_INITIALIZED.get(language, False):
        logger.debug(f"Using cached wordlist for {language} ({len(_DICTIONARY_CACHE[language])} words)")
        return _DICTIONARY_CACHE[language]
    
    # Try to load from database first (if not in test mode)
    if not os.getenv("TESTING"):
        try:
            from app.database import get_db
            from app.models.wordlist import WordList
            
            # Use database session
            db = next(get_db())
            try:
                words_query = db.query(WordList.word).filter(WordList.language == language)
                db_words = [word[0] for word in words_query.all()]
                
                if db_words:
                    word_set = set(db_words)
                    logger.info(f"Loaded {len(word_set)} words for {language} from database")
                    
                    # Cache the result
                    _DICTIONARY_CACHE[language] = word_set
                    _CACHE_INITIALIZED[language] = True
                    return word_set
                else:
                    logger.warning(f"No words found in database for language: {language}, falling back to file")
            finally:
                db.close()
                
        except Exception as e:
            logger.warning(f"Error loading from database for {language}: {e}, falling back to file")
    
    # Fall back to loading from file
    try:
        wordlist_path = get_wordlist_path(language)
        
        with open(wordlist_path, 'r', encoding='utf-8-sig') as f:
            word_set = {line.strip().upper() for line in f if line.strip()}
        
        logger.info(f"Loaded {len(word_set)} words for {language} from file: {wordlist_path}")
        
        # Cache the result
        _DICTIONARY_CACHE[language] = word_set
        _CACHE_INITIALIZED[language] = True
        return word_set
        
    except FileNotFoundError as e:
        logger.error(f"Wordlist not found for {language}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading wordlist for {language}: {e}")
        raise

def add_word_to_database(word: str, language: str, user_id: int, db: Session) -> bool:
    """Add a single word to the database and invalidate cache.
    
    Args:
        word: The word to add (will be normalized to uppercase)
        language: Language code (will be normalized to lowercase)  
        user_id: ID of the user adding the word
        db: Database session
        
    Returns:
        True if word was added, False if it already existed
        
    This function automatically invalidates the cache for the affected language.
    """
    from app.models.wordlist import WordList
    from datetime import datetime, timezone
    
    word = word.strip().upper()
    language = language.lower()
    
    # Check if word already exists
    existing_word = db.query(WordList).filter(
        WordList.word == word,
        WordList.language == language
    ).first()
    
    if existing_word:
        return False
    
    # Add the word
    new_word = WordList(
        word=word,
        language=language,
        added_user_id=user_id,
        added_timestamp=datetime.now(timezone.utc)
    )
    
    db.add(new_word)
    db.commit()
    
    # Invalidate cache for this language
    clear_wordlist_cache(language)
    
    logger.info(f"Added word '{word}' to {language} wordlist and cleared cache")
    return True

def add_words_to_database(words: list, language: str, user_id: int, db: Session) -> dict:
    """Add multiple words to the database and invalidate cache.
    
    Args:
        words: List of words to add
        language: Language code
        user_id: ID of the user adding the words
        db: Database session
        
    Returns:
        Dictionary with statistics about the operation
        
    This function automatically invalidates the cache for the affected language.
    """
    from app.models.wordlist import WordList
    from datetime import datetime, timezone
    
    language = language.lower()
    words = [word.strip().upper() for word in words if word.strip()]
    
    if not words:
        return {"total_requested": 0, "already_existing": 0, "newly_added": 0}
    
    # Check for existing words
    existing_words = db.query(WordList.word).filter(
        WordList.word.in_(words),
        WordList.language == language
    ).all()
    existing_word_set = {word[0] for word in existing_words}
    
    # Filter out existing words
    new_words = [word for word in words if word not in existing_word_set]
    
    if new_words:
        # Add new words in batch
        word_objects = [
            WordList(
                word=word,
                language=language,
                added_user_id=user_id,
                added_timestamp=datetime.now(timezone.utc)
            )
            for word in new_words
        ]
        
        db.add_all(word_objects)
        db.commit()
        
        # Invalidate cache for this language
        clear_wordlist_cache(language)
        
        logger.info(f"Added {len(new_words)} words to {language} wordlist and cleared cache")
    
    return {
        "total_requested": len(words),
        "already_existing": len(existing_word_set),
        "newly_added": len(new_words),
        "existing_words": list(existing_word_set),
        "added_words": new_words
    }
