#!/usr/bin/env python3
"""
Database migration to add join_token field to GameInvitation table.
Run this script to update your existing database schema.
"""

import sys
import os
sys.path.append('.')

from sqlalchemy import create_engine, text
from app.config import DATABASE_URL
import logging
import secrets

logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add join_token field."""
    engine = create_engine(DATABASE_URL)
    
    migration_sql = """
    -- Add join_token field to game_invitations table
    ALTER TABLE game_invitations 
    ADD COLUMN IF NOT EXISTS join_token VARCHAR UNIQUE;
    
    -- Create index on join_token for faster lookups
    CREATE INDEX IF NOT EXISTS idx_game_invitations_join_token ON game_invitations(join_token);
    """
    
    try:
        with engine.connect() as connection:
            # Execute migration in a transaction
            with connection.begin():
                connection.execute(text(migration_sql))
                
                # Update existing invitations with join tokens
                print("Updating existing invitations with join tokens...")
                
                # Get all existing invitations without join tokens
                result = connection.execute(text(
                    "SELECT id FROM game_invitations WHERE join_token IS NULL"
                ))
                
                invitation_ids = [row[0] for row in result.fetchall()]
                
                # Generate unique join tokens for existing invitations
                for invitation_id in invitation_ids:
                    join_token = secrets.token_urlsafe(32)
                    connection.execute(text(
                        "UPDATE game_invitations SET join_token = :token WHERE id = :id"
                    ), {"token": join_token, "id": invitation_id})
                
                print(f"Updated {len(invitation_ids)} existing invitations with join tokens")
                
            logger.info("Migration completed successfully")
            print("✅ Database migration completed successfully!")
            print("✅ Added join_token field to game_invitations table")
            print(f"✅ Updated {len(invitation_ids)} existing invitations")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    print("🔄 Running join_token migration...")
    print("=" * 50)
    
    try:
        run_migration()
        print("\n🎉 Migration completed successfully!")
        print("You can now use the enhanced game creation flow with email invitations.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Please check your database connection and try again.")
        sys.exit(1) 