# app/initialize.py

import os
import psycopg2
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from app.database import engine, Base, SessionLocal
from app.models import WordList
from app.config import DATABASE_URL, DEFAULT_WORDLIST_PATH
from app.wordlist import import_wordlist
import logging
import urllib.parse

logger = logging.getLogger(__name__)

def create_database():
    """Create the database if it doesn't exist."""
    # Parse the database URL to get the database name and host
    db_url = DATABASE_URL
    
    # Extract database name
    db_name = db_url.split("/")[-1]
    
    # Extract host from URL (handle URL encoding)
    parsed_url = urllib.parse.urlparse(db_url)
    host = parsed_url.hostname
    port = parsed_url.port or 5432
    user = parsed_url.username
    password = urllib.parse.unquote_plus(parsed_url.password) if parsed_url.password else ""
    
    logger.info(f"Connecting to PostgreSQL at {host}:{port}")
    
    # Create a connection to the default PostgreSQL database
    conn_string = f"postgresql://{user}:{password}@{host}:{port}/postgres"
    
    try:
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database {db_name}")
            cursor.execute(f"CREATE DATABASE {db_name}")
            logger.info(f"Database {db_name} created successfully")
        else:
            logger.info(f"Database {db_name} already exists")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False

def create_tables():
    """Create all tables defined in the models."""
    try:
        # Import all models to ensure they are registered with Base
        from app.models import User, Game, Player, Move, WordList, GameInvitation
        
        # In test mode, don't drop tables, just create if they don't exist
        if os.getenv("TESTING") == "1":
            Base.metadata.create_all(bind=engine)
        else:
            # In non-test mode, drop and recreate tables
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        expected_tables = {'users', 'games', 'players', 'moves', 'wordlists', 'game_invitations'}
        actual_tables = set(inspector.get_table_names())
        
        if not expected_tables.issubset(actual_tables):
            missing_tables = expected_tables - actual_tables
            logger.error(f"Missing tables: {missing_tables}")
            return False
            
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False

def import_default_wordlists():
    """Import default wordlists if they don't exist. For large files, import a subset initially."""
    db = SessionLocal()
    try:
        # Check if German wordlist exists
        de_count = db.query(WordList).filter(WordList.language == "de").count()
        if de_count == 0:
            logger.info(f"Checking for default German wordlist at {DEFAULT_WORDLIST_PATH}")
            if os.path.exists(DEFAULT_WORDLIST_PATH):
                logger.info("Importing German wordlist (limited to first 50,000 words for fast startup)")
                # Import only first 50,000 words for fast startup
                import_wordlist_limited("de", DEFAULT_WORDLIST_PATH, limit=50000)
                de_count = db.query(WordList).filter(WordList.language == "de").count()
                logger.info(f"Imported {de_count} German words (initial batch)")
                logger.info("Full word import will continue in background after startup")
            else:
                logger.warning(f"Default German wordlist not found at {DEFAULT_WORDLIST_PATH}")
                # Create a minimal wordlist for testing
                minimal_words = ["HALLO", "WELT", "TEST", "SPIEL", "WORT", "TAG", "TAGE", "BAUM", "HAUS", "AUTO", "TISCH", "STUHL", "ÜBER", "SCHÖN", "GRÜN"]
                for word in minimal_words:
                    db.add(WordList(word=word, language="de"))
                db.commit()
                logger.info(f"Created minimal German wordlist with {len(minimal_words)} words")
        else:
            logger.info(f"German wordlist already exists with {de_count} words")
        
        # Check for English wordlist
        en_path = "data/en_words.txt"
        if os.path.exists(en_path):
            en_count = db.query(WordList).filter(WordList.language == "en").count()
            if en_count == 0:
                logger.info("Importing English wordlist")
                import_wordlist("en", en_path)
                en_count = db.query(WordList).filter(WordList.language == "en").count()
                logger.info(f"Imported {en_count} English words")
            else:
                logger.info(f"English wordlist already exists with {en_count} words")
        else:
            logger.warning(f"English wordlist not found at {en_path}")
            # Create a minimal English wordlist
            if db.query(WordList).filter(WordList.language == "en").count() == 0:
                minimal_words = ["HELLO", "WORLD", "TEST", "GAME", "WORD", "DAY", "DAYS", "TREE", "HOUSE", "CAR", "TABLE", "CHAIR", "OVER", "NICE", "GREEN"]
                for word in minimal_words:
                    db.add(WordList(word=word, language="en"))
                db.commit()
                logger.info(f"Created minimal English wordlist with {len(minimal_words)} words")
        
        return True
    except Exception as e:
        logger.error(f"Error importing wordlists: {e}")
        return False
    finally:
        db.close()

def import_wordlist_limited(language: str, file_path: str, limit: int = 50000):
    """Import a limited number of words from a wordlist file for fast startup."""
    from app.wordlist import import_wordlist_with_limit
    return import_wordlist_with_limit(language, file_path, limit)

async def background_import_remaining_words():
    """Background task to import remaining words after startup."""
    try:
        import asyncio
        await asyncio.sleep(30)  # Wait 30 seconds after startup
        logger.info("Starting background import of remaining German words...")
        from app.wordlist import import_wordlist_continue
        import_wordlist_continue("de", DEFAULT_WORDLIST_PATH, skip=50000)
        logger.info("Background import of remaining words completed")
    except Exception as e:
        logger.error(f"Error in background word import: {e}")

def initialize_database():
    """Initialize the database and import default wordlists."""
    logger.info(f"Initializing database with URL: {DATABASE_URL}")
    
    # Check if we can connect to the database
    try:
        # Try to connect to the database
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection successful")
    except OperationalError as e:
        # Database doesn't exist, create it
        logger.info(f"Database connection failed: {e}")
        logger.info("Attempting to create database")
        if not create_database():
            logger.error("Failed to create database")
            return False
    
    # Create tables if they don't exist
    if not create_tables():
        logger.error("Failed to create tables")
        return False
    
    # Import default wordlists
    if not import_default_wordlists():
        logger.error("Failed to import default wordlists")
        return False
    
    logger.info("Database initialization complete")
    return True
