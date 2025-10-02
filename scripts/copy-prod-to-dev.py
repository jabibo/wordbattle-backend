#!/usr/bin/env python3
"""
Quick script to copy production database to dev database
This copies from wordbattle_prod to wordbattle_dev in the same Cloud SQL instance
"""

import os
import sys
import psycopg2
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker

def get_database_url(db_name: str, user: str, password: str) -> str:
    """Create database URL for Cloud SQL connection."""
    return f"postgresql+pg8000://{user}:{password}@/{db_name}?unix_sock=/cloudsql/wordbattle-secure:europe-west1:wordbattle-db"

def copy_database():
    """Copy all data from prod to dev database."""
    
    # Database credentials (same for both databases)
    user = "wordbattle"
    password = "HKrzBR4nMpF4ddgf"  # This should match the secret
    
    print("🚀 Starting database copy from production to dev...")
    
    # Create connections
    prod_url = get_database_url("wordbattle_prod", user, password)
    dev_url = get_database_url("wordbattle_dev", user, password)
    
    print(f"📊 Source: wordbattle_prod")
    print(f"🎯 Target: wordbattle_dev")
    
    try:
        # Create engines
        prod_engine = create_engine(prod_url, pool_pre_ping=True)
        dev_engine = create_engine(dev_url, pool_pre_ping=True)
        
        # Test connections
        with prod_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Production database connection successful")
        
        with dev_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Dev database connection successful")
        
        # Get table list in dependency order
        table_order = [
            'users', 
            'user_profiles',
            'user_stats',
            'games',
            'players',
            'moves',
            'game_invitations',
            'chat_messages',
            'words',
            'feedback',
            'alembic_version'
        ]
        
        # Clear dev database first
        print("🧹 Clearing dev database...")
        with dev_engine.connect() as conn:
            # Disable foreign key checks temporarily
            conn.execute(text("SET session_replication_role = replica;"))
            
            # Truncate tables in reverse order
            for table in reversed(table_order):
                try:
                    conn.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))
                    print(f"   Cleared table: {table}")
                except Exception as e:
                    print(f"   ⚠️  Could not clear {table}: {e}")
            
            # Re-enable foreign key checks
            conn.execute(text("SET session_replication_role = DEFAULT;"))
            conn.commit()
        
        # Copy data table by table
        print("📋 Copying data...")
        total_rows = 0
        
        for table in table_order:
            try:
                # Get data from production
                with prod_engine.connect() as prod_conn:
                    result = prod_conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    
                    if count == 0:
                        print(f"   ⏭️  Skipping empty table: {table}")
                        continue
                    
                    print(f"   📦 Copying {count} rows from {table}...")
                    
                    # Get all data
                    data_result = prod_conn.execute(text(f"SELECT * FROM {table}"))
                    rows = data_result.fetchall()
                    columns = data_result.keys()
                
                # Insert into dev
                if rows:
                    with dev_engine.connect() as dev_conn:
                        # Disable foreign key checks for this table
                        dev_conn.execute(text("SET session_replication_role = replica;"))
                        
                        # Build insert statement
                        col_names = ', '.join(columns)
                        placeholders = ', '.join([f':{col}' for col in columns])
                        insert_sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                        
                        # Convert rows to dictionaries
                        row_dicts = [dict(zip(columns, row)) for row in rows]
                        
                        # Execute batch insert
                        dev_conn.execute(text(insert_sql), row_dicts)
                        
                        # Re-enable foreign key checks
                        dev_conn.execute(text("SET session_replication_role = DEFAULT;"))
                        dev_conn.commit()
                        
                        total_rows += len(rows)
                        print(f"   ✅ Copied {len(rows)} rows to {table}")
                
            except Exception as e:
                print(f"   ❌ Error copying table {table}: {e}")
                continue
        
        print(f"🎉 Database copy completed! Total rows copied: {total_rows}")
        
        # Verify the copy
        print("🔍 Verifying copy...")
        with dev_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM games"))
            game_count = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM words"))
            word_count = result.scalar()
            
            print(f"✅ Dev database now contains:")
            print(f"   - Users: {user_count}")
            print(f"   - Games: {game_count}")
            print(f"   - Words: {word_count}")
    
    except Exception as e:
        print(f"❌ Database copy failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🎮 WordBattle Database Copy Tool")
    print("================================")
    print("This will copy all data from wordbattle_prod to wordbattle_dev")
    print("⚠️  WARNING: This will overwrite all data in the dev database!")
    print()
    
    response = input("Continue? (type 'yes' to confirm): ")
    if response.lower() != 'yes':
        print("Operation cancelled.")
        sys.exit(0)
    
    success = copy_database()
    sys.exit(0 if success else 1)

