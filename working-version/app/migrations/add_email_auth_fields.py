"""
Database migration to add email authentication fields to User table.
Run this script to update your existing database schema.
"""

from sqlalchemy import create_engine, text
from app.config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add email authentication fields."""
    engine = create_engine(DATABASE_URL)
    
    migration_sql = """
    -- Add email authentication fields to users table
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE,
    ADD COLUMN IF NOT EXISTS verification_code VARCHAR,
    ADD COLUMN IF NOT EXISTS verification_code_expires TIMESTAMP,
    ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS persistent_token VARCHAR,
    ADD COLUMN IF NOT EXISTS persistent_token_expires TIMESTAMP,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
    
    -- Make hashed_password nullable for email-only auth
    ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;
    
    -- Create index on email for faster lookups
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_persistent_token ON users(persistent_token);
    """
    
    try:
        with engine.connect() as connection:
            # Execute migration in a transaction
            with connection.begin():
                connection.execute(text(migration_sql))
            logger.info("Migration completed successfully")
            print("✅ Database migration completed successfully!")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration() 