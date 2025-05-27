from typing import Set
from app.config import DEFAULT_WORDLIST_PATH
from app.database import SessionLocal
from app.models import WordList
import os
import codecs

def load_wordlist_from_file(path: str = None) -> Set[str]:
    """
    Load a wordlist from a file with proper UTF-8 handling.
    
    Args:
        path: Path to the wordlist file. If None, uses the default path from config.
        
    Returns:
        A set of uppercase words from the file.
    """
    if path is None:
        path = DEFAULT_WORDLIST_PATH
    
    # Try different encodings in order of preference
    encodings = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            with codecs.open(path, 'r', encoding=encoding) as f:
                return {line.strip().upper() for line in f if line.strip()}
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            raise FileNotFoundError(f"Wordlist file not found: {path}")
    
    # If all encodings fail, try binary mode with UTF-8 and ignore errors
    try:
        with open(path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
            return {line.strip().upper() for line in content.splitlines() if line.strip()}
    except Exception as e:
        raise RuntimeError(f"Failed to load wordlist from {path}: {str(e)}")

def load_wordlist(language="de") -> set[str]:
    """
    Load a wordlist for the specified language.
    
    This function redirects to the unified load_wordlist in utils.wordlist_utils
    for consistency across the application.
    
    Args:
        language: Language code (e.g., "de", "en")
        
    Returns:
        A set of uppercase words.
    """
    from app.utils.wordlist_utils import load_wordlist as unified_load_wordlist
    return unified_load_wordlist(language)

def import_wordlist(language: str = "de", path: str = None) -> None:
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
    db = SessionLocal()
    try:
        # Clear existing words for this language
        db.query(WordList).filter(WordList.language == language).delete()
        
        # Batch insert for better performance
        batch_size = 1000
        word_list = list(words)
        total_words = len(word_list)
        
        for i in range(0, total_words, batch_size):
            batch = [WordList(word=word, language=language) 
                    for word in word_list[i:i+batch_size]]
            db.add_all(batch)
            db.commit()
            print(f"Imported {min(i+batch_size, total_words)}/{total_words} words")
        
        print(f"Successfully imported {total_words} words for language '{language}'")
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Failed to import wordlist: {str(e)}")
    finally:
        db.close()

def import_wordlist_with_limit(language: str, path: str, limit: int = 50000) -> None:
    """
    Import a limited number of words from a wordlist file for fast startup.
    
    Args:
        language: Language code (e.g., "de", "en")
        path: Path to the wordlist file
        limit: Maximum number of words to import
    """
    # Load words from file (limited)
    encodings = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252']
    words = []
    
    for encoding in encodings:
        try:
            with codecs.open(path, 'r', encoding=encoding) as f:
                for i, line in enumerate(f):
                    if i >= limit:
                        break
                    word = line.strip().upper()
                    if word:
                        words.append(word)
            break
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            raise FileNotFoundError(f"Wordlist file not found: {path}")
    
    # Import to database
    db = SessionLocal()
    try:
        # Clear existing words for this language
        db.query(WordList).filter(WordList.language == language).delete()
        
        # Batch insert for better performance
        batch_size = 1000
        total_words = len(words)
        
        for i in range(0, total_words, batch_size):
            batch = [WordList(word=word, language=language) 
                    for word in words[i:i+batch_size]]
            db.add_all(batch)
            db.commit()
            print(f"Imported {min(i+batch_size, total_words)}/{total_words} words")
        
        print(f"Successfully imported {total_words} words for language '{language}' (limited import)")
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Failed to import limited wordlist: {str(e)}")
    finally:
        db.close()

def import_wordlist_continue(language: str, path: str, skip: int = 0) -> None:
    """
    Continue importing words from where a previous limited import left off.
    
    Args:
        language: Language code (e.g., "de", "en")
        path: Path to the wordlist file
        skip: Number of words to skip (from previous import)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting background import for {language}, skipping first {skip} words")
    
    # Load remaining words from file
    encodings = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252']
    words = []
    
    for encoding in encodings:
        try:
            with codecs.open(path, 'r', encoding=encoding) as f:
                for i, line in enumerate(f):
                    if i < skip:
                        continue
                    word = line.strip().upper()
                    if word:
                        words.append(word)
            break
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            logger.error(f"Wordlist file not found: {path}")
            return
    
    if not words:
        logger.info("No additional words to import")
        return
    
    # Import to database (append mode)
    db = SessionLocal()
    try:
        # Batch insert for better performance
        batch_size = 1000
        total_words = len(words)
        
        for i in range(0, total_words, batch_size):
            batch = [WordList(word=word, language=language) 
                    for word in words[i:i+batch_size]]
            db.add_all(batch)
            db.commit()
            
            if i % 10000 == 0:  # Log every 10k words
                logger.info(f"Background import: {skip + i + batch_size}/{skip + total_words} total words")
        
        logger.info(f"Background import completed: {total_words} additional words imported for language '{language}'")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to continue wordlist import: {str(e)}")
    finally:
        db.close()

def get_wordlist(language: str = "de") -> Set[str]:
    """
    Get all words for a given language from the database.
    
    Args:
        language: Language code (e.g., "de", "en")
    
    Returns:
        A set of uppercase words for the specified language.
    """
    db = SessionLocal()
    try:
        words = db.query(WordList.word).filter(WordList.language == language).all()
        return {word[0].upper() for word in words}
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
