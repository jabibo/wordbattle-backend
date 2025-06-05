#!/usr/bin/env python3
"""
Migration script to add language field to users table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add language field to users table with default value 'en'"""
    db = SessionLocal()
    
    try:
        logger.info("Starting migration: Adding language field to users table")
        
        # Check if column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'language'
        """))
        
        if result.fetchone():
            logger.info("Language column already exists, skipping migration")
            return True
        
        # Add language column with default value
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN language VARCHAR DEFAULT 'en'
        """))
        
        # Update existing users to have default language
        db.execute(text("""
            UPDATE users 
            SET language = 'en' 
            WHERE language IS NULL
        """))
        
        db.commit()
        logger.info("Migration completed successfully: language field added to users table")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 