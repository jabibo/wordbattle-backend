#!/usr/bin/env python3
"""
Migration script to copy all data from current production database 
(wordbattle-1748668162:wordbattle_db) to secure production database 
(wordbattle-secure:wordbattle_prod)
"""

import os
import sys
import time
import argparse
from typing import List, Dict, Any

# Database connection imports
import psycopg2
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker

def get_database_url(project_id: str, db_name: str, user: str, password: str, instance: str) -> str:
    """Create database URL for Cloud SQL connection."""
    return f"postgresql+pg8000://{user}:{password}@/{db_name}?unix_sock=/cloudsql/{project_id}:europe-west1:{instance}"

def create_direct_connection(project_id: str, db_name: str, user: str, password: str, instance: str):
    """Create direct psycopg2 connection for Cloud SQL."""
    return psycopg2.connect(
        host=f"/cloudsql/{project_id}:europe-west1:{instance}",
        database=db_name,
        user=user,
        password=password
    )

def get_table_list(engine) -> List[str]:
    """Get list of all tables in the database, in dependency order."""
    # Order matters for foreign key constraints
    table_order = [
        'alembic_version',
        'users', 
        'user_profiles',
        'user_stats',
        'games',
        'players',
        'moves',
        'game_invitations',
        'chat_messages',
        'words',
        'feedback'
    ]
    
    # Get all tables that actually exist
    metadata = MetaData()
    metadata.reflect(bind=engine)
    existing_tables = list(metadata.tables.keys())
    
    # Return ordered list of existing tables
    ordered_existing = [table for table in table_order if table in existing_tables]
    # Add any tables not in our predefined order
    remaining_tables = [table for table in existing_tables if table not in table_order]
    
    return ordered_existing + remaining_tables

def copy_table_data(source_engine, target_engine, table_name: str, batch_size: int = 1000):
    """Copy all data from source table to target table."""
    print(f"📋 Copying table: {table_name}")
    
    # Get row count
    with source_engine.connect() as conn:
        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        total_rows = count_result.scalar()
    
    if total_rows == 0:
        print(f"   ✅ Table {table_name} is empty, skipping")
        return True
    
    print(f"   📊 Total rows to copy: {total_rows}")
    
    try:
        # Get column names
        with source_engine.connect() as conn:
            columns_result = conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in columns_result]
        
        column_list = ", ".join(f'"{col}"' for col in columns)
        
        # Clear target table first
        with target_engine.connect() as conn:
            conn.execute(text(f'DELETE FROM "{table_name}"'))
            conn.commit()
        
        # Copy data in batches
        offset = 0
        while offset < total_rows:
            # Fetch batch from source
            with source_engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT {column_list} 
                    FROM "{table_name}" 
                    ORDER BY 1 
                    LIMIT {batch_size} OFFSET {offset}
                """))
                rows = result.fetchall()
            
            if not rows:
                break
            
            # Insert batch into target
            placeholders = ", ".join(["%s"] * len(columns))
            insert_sql = f'INSERT INTO "{table_name}" ({column_list}) VALUES ({placeholders})'
            
            # Use direct psycopg2 for better performance
            target_conn = create_direct_connection(
                "wordbattle-secure", "wordbattle_prod", "wordbattle", "HKrzBR4nMpF4ddgf", "wordbattle-db"
            )
            try:
                with target_conn.cursor() as cursor:
                    cursor.executemany(insert_sql, rows)
                    target_conn.commit()
            finally:
                target_conn.close()
            
            offset += len(rows)
            print(f"   📦 Copied {offset}/{total_rows} rows")
        
        print(f"   ✅ Table {table_name} copied successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Error copying table {table_name}: {e}")
        return False

def migrate_data(dry_run: bool = False, verbose: bool = False):
    """Main migration function."""
    print("🚀 WordBattle Production to Secure Production Migration")
    print("=" * 60)
    print()
    
    # Source: Current production database
    source_url = get_database_url(
        "wordbattle-1748668162", "wordbattle_db", "wordbattle", "HKrzBR4nMpF4ddgf", "wordbattle-db"
    )
    
    # Target: Secure production database  
    target_url = get_database_url(
        "wordbattle-secure", "wordbattle_prod", "wordbattle", "HKrzBR4nMpF4ddgf", "wordbattle-db"
    )
    
    print(f"📍 Source: wordbattle-1748668162:wordbattle_db")
    print(f"📍 Target: wordbattle-secure:wordbattle_prod")
    print()
    
    if dry_run:
        print("🔍 DRY RUN MODE - No data will be modified")
        print()
    
    try:
        # Create engine connections
        print("🔌 Connecting to databases...")
        source_engine = create_engine(source_url, echo=verbose)
        target_engine = create_engine(target_url, echo=verbose)
        
        # Test connections
        with source_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Source database connection successful")
        
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Target database connection successful")
        print()
        
        if dry_run:
            print("🔍 Would copy the following tables:")
            tables = get_table_list(source_engine)
            for table in tables:
                with source_engine.connect() as conn:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                print(f"   📋 {table}: {count} rows")
            print()
            print("✅ Dry run completed - no data was copied")
            return True
        
        # Get tables to copy
        tables = get_table_list(source_engine)
        print(f"📋 Found {len(tables)} tables to migrate")
        print()
        
        # Copy each table
        success_count = 0
        for table in tables:
            if copy_table_data(source_engine, target_engine, table):
                success_count += 1
            print()
        
        print("=" * 60)
        print(f"✅ Migration completed!")
        print(f"📊 Successfully copied {success_count}/{len(tables)} tables")
        
        if success_count == len(tables):
            print("🎉 All data migrated successfully to secure production!")
            return True
        else:
            print("⚠️  Some tables had errors - please review the output above")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate production data to secure production")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose SQL logging")
    
    args = parser.parse_args()
    
    if not args.dry_run:
        print("🚨 WARNING: This will copy ALL production data to the secure production database!")
        print("🚨 This will OVERWRITE any existing data in the target database!")
        print()
        response = input("Are you sure you want to proceed? Type 'MIGRATE PROD' to continue: ")
        if response != "MIGRATE PROD":
            print("❌ Migration cancelled")
            return 1
    
    success = migrate_data(dry_run=args.dry_run, verbose=args.verbose)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
