#!/usr/bin/env python3
"""
Script to reset migration state and run all migrations properly.
This handles the case where tables were created outside of Alembic.
"""
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic.config import Config
from alembic import command
from sqlalchemy import text
from app.database import SessionLocal, engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_and_run_migrations():
    """Reset migration state and run all migrations"""
    try:
        # Get alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Drop the alembic_version table if it exists
        logger.info("Dropping alembic_version table if it exists...")
        db = SessionLocal()
        try:
            db.execute(text("DROP TABLE IF EXISTS alembic_version"))
            db.commit()
            logger.info("✅ Alembic version table dropped")
        except Exception as e:
            logger.warning(f"Could not drop alembic_version table: {e}")
            db.rollback()
        finally:
            db.close()
        
        # Now run all migrations from the beginning
        logger.info("Running all migrations from scratch...")
        command.upgrade(alembic_cfg, "head")
        
        logger.info("✅ All migrations completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration reset failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Resetting migration state and running all migrations...")
    success = reset_and_run_migrations()
    
    if success:
        print("🎉 Migration reset completed successfully!")
    else:
        print("❌ Migration reset failed!")
        sys.exit(1) 