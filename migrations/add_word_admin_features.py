"""
Database migration to add word admin features.
Run this script to update your existing database schema.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add word admin features."""
    engine = create_engine(DATABASE_URL)
    
    migration_sql = """
    -- Add word admin field to users table
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS is_word_admin BOOLEAN DEFAULT FALSE;
    
    -- Add tracking fields to wordlists table
    ALTER TABLE wordlists 
    ADD COLUMN IF NOT EXISTS added_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS added_user_id INTEGER REFERENCES users(id);
    
    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_users_word_admin ON users(is_word_admin);
    CREATE INDEX IF NOT EXISTS idx_wordlists_added_user ON wordlists(added_user_id);
    CREATE INDEX IF NOT EXISTS idx_wordlists_added_timestamp ON wordlists(added_timestamp);
    
    -- Set added_timestamp for existing words to creation time (approximation)
    UPDATE wordlists 
    SET added_timestamp = CURRENT_TIMESTAMP 
    WHERE added_timestamp IS NULL;
    """
    
    try:
        with engine.connect() as connection:
            # Execute migration in a transaction
            with connection.begin():
                connection.execute(text(migration_sql))
            logger.info("Word admin migration completed successfully")
            print("✅ Word admin database migration completed successfully!")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration() 