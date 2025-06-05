#!/usr/bin/env python3
"""
Database management utilities for WordBattle backend.
Provides functions to check database status, reset database, and manage word loading.
"""
import logging
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal, engine, Base
from app.models import WordList, User, Game
from app.wordlist import import_wordlist_continue
from app.config import DEFAULT_WORDLIST_PATH
import os

logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run Alembic migrations automatically during startup.
    
    Returns:
        dict: Migration results with success status and info
    """
    try:
        logger.info("Running database migrations...")
        
        # Import alembic components
        from alembic.config import Config
        from alembic import command
        from alembic.script import ScriptDirectory
        
        # Get alembic config file path (relative to project root)
        alembic_cfg = Config("alembic.ini")
        
        # Check current revision
        try:
            current_rev = command.current(alembic_cfg)
            logger.info(f"Current database revision: {current_rev}")
        except Exception as e:
            logger.info(f"Could not get current revision (probably no version table): {e}")
            current_rev = None
        
        # Get target revision (head)
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script_dir.get_current_head()
        logger.info(f"Target revision (head): {head_rev}")
        
        # If database has no version table, we need to handle the migration state properly
        if current_rev is None:
            try:
                # Check if tables already exist
                from sqlalchemy import inspect
                inspector = inspect(engine)
                existing_tables = inspector.get_table_names()
                
                if len(existing_tables) > 1:  # More than just alembic_version
                    logger.info("Database has tables but no version info")
                    
                    # Check if friends table exists - if so, stamp with 0007 (before friends removal)
                    if "friends" in existing_tables:
                        logger.info("Friends table exists - stamping with revision 0007")
                        command.stamp(alembic_cfg, "0007")
                        # Now run remaining migrations (0008 to drop friends)
                        command.upgrade(alembic_cfg, "head")
                    else:
                        # No friends table, stamp with latest
                        logger.info("No friends table - stamping with head")
                        command.stamp(alembic_cfg, "head")
                    
                    logger.info("✅ Database migration state fixed and updated")
                    return {
                        "success": True,
                        "action": "fixed_and_upgraded",
                        "message": "Database migration state fixed and upgraded to head"
                    }
                else:
                    # Empty database or only alembic_version - run all migrations
                    logger.info("Empty database - running all migrations")
                    command.upgrade(alembic_cfg, "head")
                    
            except Exception as stamp_error:
                logger.warning(f"Could not fix migration state: {stamp_error}")
                # Fallback - try to run migrations anyway
                command.upgrade(alembic_cfg, "head")
        else:
            # Normal case - database has version info, just upgrade
            command.upgrade(alembic_cfg, "head")
        
        logger.info("✅ Database migrations completed successfully")
        return {
            "success": True,
            "action": "completed",
            "message": "Migrations run successfully"
        }
        
    except ImportError as e:
        logger.error(f"❌ Alembic not available: {e}")
        return {
            "success": False,
            "action": "skipped",
            "error": "Alembic not installed",
            "message": "Migrations skipped - Alembic not available"
        }
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return {
            "success": False,
            "action": "failed", 
            "error": str(e),
            "message": f"Migration error: {str(e)}"
        }

def check_database_status():
    """
    Check the current status of the database.
    
    Returns:
        dict: Database status information including:
            - tables_exist: bool
            - word_counts: dict with counts per language
            - user_count: int
            - game_count: int
            - is_initialized: bool
    """
    status = {
        "tables_exist": False,
        "word_counts": {},
        "user_count": 0,
        "game_count": 0,
        "is_initialized": False
    }
    
    db = SessionLocal()
    try:
        # Check if tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        expected_tables = ["users", "games", "wordlists", "players", "moves", "game_invitations", "chat_messages"]
        
        status["tables_exist"] = all(table in existing_tables for table in expected_tables)
        
        if status["tables_exist"]:
            # Count words by language
            word_counts = db.execute(
                text("SELECT language, COUNT(*) as count FROM wordlists GROUP BY language")
            ).fetchall()
            status["word_counts"] = {row.language: row.count for row in word_counts}
            
            # Count users and games
            status["user_count"] = db.query(User).count()
            status["game_count"] = db.query(Game).count()
            
            # Consider database initialized if we have tables and some words
            status["is_initialized"] = (
                status["tables_exist"] and 
                sum(status["word_counts"].values()) > 1000  # At least 1000 words loaded
            )
        
        logger.info(f"Database status check completed: {status}")
        return status
        
    except SQLAlchemyError as e:
        logger.error(f"Database status check failed: {e}")
        return status
    finally:
        db.close()

def reset_database(confirm=False):
    """
    Reset the database by dropping and recreating all tables.
    
    Args:
        confirm (bool): Must be True to actually perform the reset
        
    Returns:
        bool: True if reset was successful, False otherwise
    """
    if not confirm:
        logger.warning("Database reset called without confirmation - no action taken")
        return False
    
    try:
        logger.info("Starting database reset...")
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")
        
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        logger.info("All tables recreated")
        
        logger.info("Database reset completed successfully")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database reset failed: {e}")
        return False

def load_wordlist(language="de", wordlist_path=None, skip=0, limit=None):
    """
    Load words from wordlist file into the database.
    
    Args:
        language (str): Language code (e.g., "de", "en")
        wordlist_path (str): Path to wordlist file (uses default if None)
        skip (int): Number of words to skip (for resuming)
        limit (int): Maximum number of words to load (None for all)
        
    Returns:
        dict: Loading results with counts and status
    """
    if wordlist_path is None:
        wordlist_path = DEFAULT_WORDLIST_PATH
    
    if not os.path.exists(wordlist_path):
        logger.error(f"Wordlist file not found: {wordlist_path}")
        return {"success": False, "error": "Wordlist file not found"}
    
    try:
        logger.info(f"Starting wordlist loading: language={language}, skip={skip}, limit={limit}")
        
        # Get initial count
        db = SessionLocal()
        try:
            initial_count = db.query(WordList).filter(WordList.language == language).count()
        finally:
            db.close()
        
        # Load words
        result = import_wordlist_continue(language, wordlist_path, skip=skip, limit=limit)
        
        # Get final count
        db = SessionLocal()
        try:
            final_count = db.query(WordList).filter(WordList.language == language).count()
        finally:
            db.close()
        
        words_loaded = final_count - initial_count
        
        logger.info(f"Wordlist loading completed: {words_loaded} words loaded")
        
        return {
            "success": True,
            "words_loaded": words_loaded,
            "total_words": final_count,
            "language": language
        }
        
    except Exception as e:
        logger.error(f"Wordlist loading failed: {e}")
        return {"success": False, "error": str(e)}

def initialize_database_if_needed():
    """
    Initialize database only if it's not already set up.
    This is the smart initialization function that checks before doing work.
    Now includes automatic migrations.
    
    Returns:
        dict: Initialization results
    """
    logger.info("Checking if database initialization is needed...")
    
    # First, run migrations (this is safe to run multiple times)
    migration_result = run_migrations()
    if not migration_result["success"] and migration_result["action"] != "skipped":
        logger.warning(f"Migration issues (continuing anyway): {migration_result.get('error', 'Unknown')}")
    
    status = check_database_status()
    
    if status["is_initialized"]:
        logger.info("Database is already initialized - skipping initialization")
        return {
            "success": True,
            "action": "skipped",
            "reason": "already_initialized",
            "status": status,
            "migration": migration_result
        }
    
    logger.info("Database needs initialization...")
    
    try:
        # Create tables if they don't exist
        if not status["tables_exist"]:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
        
        # Load initial words if needed
        word_count = sum(status["word_counts"].values())
        if word_count < 1000:  # Load words if we have less than 1000
            logger.info("Loading initial wordlist...")
            load_result = load_wordlist(language="de", limit=10000)  # Load first 10k words
            
            if not load_result["success"]:
                return {
                    "success": False,
                    "action": "failed",
                    "error": load_result.get("error", "Unknown error"),
                    "migration": migration_result
                }
        
        logger.info("Database initialization completed successfully")
        return {
            "success": True,
            "action": "completed",
            "message": "Database initialized successfully",
            "migration": migration_result
        }
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return {
            "success": False,
            "action": "failed",
            "error": str(e),
            "migration": migration_result
        }

def get_database_info():
    """
    Get comprehensive database information for debugging/monitoring.
    
    Returns:
        dict: Detailed database information
    """
    info = {
        "status": check_database_status(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_url": os.getenv("DATABASE_URL", "").split("@")[-1] if os.getenv("DATABASE_URL") else "local",
    }
    
    # Add table sizes if database is accessible
    if info["status"]["tables_exist"]:
        db = SessionLocal()
        try:
            # Get table row counts
            tables_info = {}
            inspector = inspect(engine)
            for table_name in inspector.get_table_names():
                try:
                    count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                    tables_info[table_name] = count
                except Exception as e:
                    tables_info[table_name] = f"Error: {e}"
            
            info["tables"] = tables_info
        finally:
            db.close()
    
    return info

# CLI-style functions for manual management
def cli_reset_database():
    """CLI function to reset database with confirmation prompt."""
    print("⚠️  WARNING: This will delete ALL data in the database!")
    print("This action cannot be undone.")
    
    confirm = input("Type 'RESET' to confirm: ").strip()
    if confirm == "RESET":
        result = reset_database(confirm=True)
        if result:
            print("✅ Database reset successfully")
        else:
            print("❌ Database reset failed")
    else:
        print("❌ Reset cancelled")

def cli_load_words(language="de", limit=None):
    """CLI function to load words with progress feedback."""
    print(f"🔤 Loading words for language: {language}")
    if limit:
        print(f"📊 Limit: {limit} words")
    
    result = load_wordlist(language=language, limit=limit)
    
    if result["success"]:
        print(f"✅ Loaded {result['words_loaded']} words")
        print(f"📊 Total words in database: {result['total_words']}")
    else:
        print(f"❌ Failed to load words: {result.get('error', 'Unknown error')}")

def cli_database_status():
    """CLI function to display database status."""
    print("🔍 Database Status")
    print("=" * 30)
    
    info = get_database_info()
    status = info["status"]
    
    print(f"📊 Tables exist: {'✅' if status['tables_exist'] else '❌'}")
    print(f"🔧 Initialized: {'✅' if status['is_initialized'] else '❌'}")
    print(f"👥 Users: {status['user_count']}")
    print(f"🎮 Games: {status['game_count']}")
    
    if status["word_counts"]:
        print("🔤 Words by language:")
        for lang, count in status["word_counts"].items():
            print(f"   {lang}: {count:,}")
    else:
        print("🔤 No words loaded")
    
    if "tables" in info:
        print("\n📋 Table sizes:")
        for table, count in info["tables"].items():
            print(f"   {table}: {count}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python database_manager.py <command>")
        print("Commands:")
        print("  status    - Show database status")
        print("  reset     - Reset database (with confirmation)")
        print("  load      - Load words (default: German)")
        print("  load-en   - Load English words")
        print("  init      - Smart initialization (only if needed)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        cli_database_status()
    elif command == "reset":
        cli_reset_database()
    elif command == "load":
        cli_load_words("de")
    elif command == "load-en":
        cli_load_words("en")
    elif command == "init":
        result = initialize_database_if_needed()
        if result["success"]:
            print(f"✅ Database initialization: {result['action']}")
        else:
            print(f"❌ Database initialization failed: {result.get('error', 'Unknown error')}")
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1) 