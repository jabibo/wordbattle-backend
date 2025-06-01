#!/usr/bin/env python3
"""
Run word admin migration on Google Cloud SQL database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Cloud SQL database connection parameters
DB_HOST = "35.187.90.105"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "Wordbattle2024"
DB_NAME = "wordbattle_db"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def run_word_admin_migration():
    """Run the migration to add word admin features to Google Cloud SQL."""
    print("🔧 Running word admin migration on Google Cloud SQL...")
    print(f"Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    migration_sql = """
    -- Add word admin field to users table
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS is_word_admin BOOLEAN DEFAULT FALSE;
    
    -- Add tracking fields to wordlists table (if wordlists table exists)
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
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Execute migration in a transaction
            with connection.begin():
                connection.execute(text(migration_sql))
                
        logger.info("Word admin migration completed successfully")
        print("✅ Word admin database migration completed successfully!")
        print()
        print("🎯 Changes made:")
        print("  - Added is_word_admin column to users table")
        print("  - Added tracking fields to wordlists table") 
        print("  - Created performance indexes")
        print()
        print("🧪 Now you can test the debug tokens endpoint:")
        print("  curl https://wordbattle-backend-skhco4fxoq-ew.a.run.app/debug/tokens")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_word_admin_migration()
    sys.exit(0 if success else 1) 