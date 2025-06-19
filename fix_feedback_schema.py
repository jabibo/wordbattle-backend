#!/usr/bin/env python3
"""
Fix feedback table schema mismatch between migration and model.
Migration created user_id as String, but model expects Integer.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import get_db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_feedback_schema():
    """Fix the feedback table schema mismatch"""
    db = next(get_db())
    
    try:
        # Check current schema
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'feedback' AND column_name = 'user_id'
        """))
        current_schema = result.fetchone()
        
        if current_schema:
            logger.info(f"Current user_id type: {current_schema[1]}")
            
            if current_schema[1] in ['character varying', 'text', 'varchar']:
                logger.info("Found String type user_id, converting to Integer...")
                
                # Drop and recreate the table with correct schema
                fix_sql = """
                -- Backup existing data if any
                CREATE TEMP TABLE feedback_backup AS SELECT * FROM feedback;
                
                -- Drop existing table
                DROP TABLE IF EXISTS feedback;
                
                -- Create feedback table with correct schema
                CREATE TABLE feedback (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    category feedbackcategory NOT NULL,
                    description TEXT NOT NULL,
                    contact_email VARCHAR(255),
                    debug_logs JSON,
                    device_info JSON,
                    app_info JSON,
                    status feedbackstatus NOT NULL DEFAULT 'new',
                    admin_notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
                CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(category);
                CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
                CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
                
                -- Restore data if any (convert user_id to integer if possible)
                INSERT INTO feedback SELECT 
                    id, 
                    CAST(user_id AS INTEGER),
                    category,
                    description,
                    contact_email,
                    debug_logs,
                    device_info,
                    app_info,
                    status,
                    admin_notes,
                    created_at,
                    updated_at
                FROM feedback_backup 
                WHERE user_id ~ '^[0-9]+$';  -- Only insert rows where user_id is numeric
                """
                
                db.execute(text(fix_sql))
                db.commit()
                logger.info("✅ Feedback schema fixed successfully!")
                
            else:
                logger.info("✅ Schema is already correct (Integer type)")
        else:
            logger.info("❌ Feedback table not found")
            
    except Exception as e:
        logger.error(f"❌ Error fixing schema: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_feedback_schema() 