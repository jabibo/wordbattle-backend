#!/usr/bin/env python3
"""
Check Migration Status and Apply if Needed
This script checks the current Alembic migration state and applies pending migrations.
"""

import os
import sys
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext
from sqlalchemy import create_engine, text

def check_migration_status():
    """Check current migration status and apply pending migrations."""
    
    print("🔍 Checking Migration Status...")
    
    # Database URL for production - Use the proper Cloud SQL proxy format
    database_url = "postgresql://wordbattle_user:wordbattle_password@/cloudsql/wordbattle-1748668162:europe-west1:wordbattle-db/wordbattle_db"
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Check if alembic_version table exists and get current revision
        with engine.connect() as conn:
            try:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                current_revision = result.fetchone()
                if current_revision:
                    current_revision = current_revision[0]
                    print(f"📋 Current database revision: {current_revision}")
                else:
                    print("⚠️  No current revision found in alembic_version table")
                    current_revision = None
            except Exception as e:
                print(f"⚠️  Could not read alembic_version table: {e}")
                current_revision = None
        
        # Get Alembic configuration
        alembic_cfg = Config("alembic.ini")
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        
        # Get head revision
        head_revision = script_dir.get_current_head()
        print(f"📋 Head revision: {head_revision}")
        
        # Check if migration is needed
        if current_revision != head_revision:
            print("⚠️  Database is not up to date!")
            print(f"   Current: {current_revision}")
            print(f"   Head: {head_revision}")
            
            # Apply migrations
            print("🔧 Applying pending migrations...")
            command.upgrade(alembic_cfg, "head")
            print("✅ Migrations applied successfully!")
        else:
            print("✅ Database is up to date!")
        
        # Verify the games table has the required columns
        print("\n🔍 Verifying games table schema...")
        with engine.connect() as conn:
            try:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'games' 
                    ORDER BY column_name
                """))
                columns = [row[0] for row in result.fetchall()]
                print(f"📋 Games table columns: {columns}")
                
                required_columns = ['name', 'ended_at']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    print(f"❌ Missing columns: {missing_columns}")
                    
                    # Manually add missing columns
                    print("🔧 Adding missing columns...")
                    for col in missing_columns:
                        if col == 'name':
                            conn.execute(text("ALTER TABLE games ADD COLUMN name VARCHAR"))
                            print("✅ Added 'name' column")
                        elif col == 'ended_at':
                            conn.execute(text("ALTER TABLE games ADD COLUMN ended_at TIMESTAMP WITH TIME ZONE"))
                            print("✅ Added 'ended_at' column")
                    conn.commit()
                else:
                    print("✅ All required columns present!")
                    
            except Exception as e:
                print(f"❌ Error checking table schema: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Migration Status Checker")
    print("=" * 40)
    
    # Set environment
    os.environ["ENVIRONMENT"] = "production"
    
    success = check_migration_status()
    
    if success:
        print("\n🎉 Migration check completed successfully!")
    else:
        print("\n❌ Migration check failed!")
        sys.exit(1) 