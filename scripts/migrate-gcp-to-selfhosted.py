#!/usr/bin/env python3
"""
Migration script to copy all data from GCP production database 
(wordbattle-secure:wordbattle_prod) to self-hosted server (wordbattle2.de)
"""

import os
import sys
import time
import argparse
import subprocess
from typing import List, Dict, Any

# Database connection imports
import psycopg2
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker

# Configuration
GCP_PROJECT = "wordbattle-secure"
GCP_INSTANCE = "wordbattle-db"
GCP_DB_NAME = "wordbattle_prod"
GCP_DB_USER = "wordbattle"
GCP_DB_PASSWORD = "p2n1kqcYFLbx51nsbhUkMYzAHz8oWUGOfwvK3H+okVI="

SELFHOST_HOST = "127.0.0.1"  # Via SSH tunnel on port 5434
SELFHOST_PORT = 5434
SELFHOST_DB_NAME = "wordbattle_prod"
SELFHOST_DB_USER = "wordbattle_user"
SELFHOST_DB_PASSWORD = "c6976e0feda09e8660c47965334f98df345547c38a17ded4e76969834b425be7"

def start_cloud_sql_proxy():
    """Start Cloud SQL Proxy for GCP connection."""
    connection_name = f"{GCP_PROJECT}:europe-west1:{GCP_INSTANCE}"
    proxy_cmd = f"./cloud_sql_proxy -instances={connection_name}=tcp:5433"
    
    print("🔌 Starting Cloud SQL Proxy...")
    proxy_process = subprocess.Popen(
        proxy_cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/Users/janbinge/git/wordbattle/wordbattle-backend"
    )
    
    # Wait for proxy to start
    time.sleep(5)
    print("✅ Cloud SQL Proxy started")
    return proxy_process

def create_source_connection():
    """Create connection to GCP Cloud SQL via proxy."""
    return psycopg2.connect(
        host="127.0.0.1",
        port=5433,
        database=GCP_DB_NAME,
        user=GCP_DB_USER,
        password=GCP_DB_PASSWORD
    )

def create_target_connection():
    """Create connection to self-hosted server."""
    return psycopg2.connect(
        host=SELFHOST_HOST,
        port=SELFHOST_PORT,
        database=SELFHOST_DB_NAME,
        user=SELFHOST_DB_USER,
        password=SELFHOST_DB_PASSWORD
    )

def get_source_engine():
    """Get SQLAlchemy engine for source database."""
    return create_engine(
        f"postgresql://{GCP_DB_USER}:{GCP_DB_PASSWORD}@127.0.0.1:5433/{GCP_DB_NAME}"
    )

def get_target_engine():
    """Get SQLAlchemy engine for target database."""
    return create_engine(
        f"postgresql://{SELFHOST_DB_USER}:{SELFHOST_DB_PASSWORD}@{SELFHOST_HOST}:{SELFHOST_PORT}/{SELFHOST_DB_NAME}"
    )

def get_table_list(engine) -> List[str]:
    """Get list of all tables in the database, in dependency order."""
    # Order matters for foreign key constraints
    table_order = [
        'alembic_version',
        'users', 
        'user_profiles',
        'user_stats',
        'wordlists',
        'games',
        'players',
        'moves',
        'game_invitations',
        'chat_messages',
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
    
    print(f"   📊 Total rows to copy: {total_rows:,}")
    
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
        print(f"   🗑️  Clearing target table...")
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
            target_conn = create_target_connection()
            try:
                with target_conn.cursor() as cursor:
                    cursor.executemany(insert_sql, rows)
                    target_conn.commit()
            finally:
                target_conn.close()
            
            offset += len(rows)
            percent = (offset / total_rows) * 100
            print(f"   📦 Copied {offset:,}/{total_rows:,} rows ({percent:.1f}%)")
        
        print(f"   ✅ Table {table_name} copied successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Error copying table {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_data(dry_run: bool = False, verbose: bool = False):
    """Main migration function."""
    print("🚀 WordBattle GCP to Self-Hosted Migration")
    print("=" * 60)
    print()
    
    print(f"📍 Source: GCP Cloud SQL ({GCP_PROJECT}:{GCP_DB_NAME})")
    print(f"📍 Target: Self-Hosted ({SELFHOST_HOST})")
    print()
    
    if dry_run:
        print("🔍 DRY RUN MODE - No data will be modified")
        print()
    
    proxy_process = None
    
    try:
        # Start Cloud SQL Proxy
        proxy_process = start_cloud_sql_proxy()
        
        # Create engine connections
        print("🔌 Connecting to databases...")
        source_engine = get_source_engine()
        target_engine = get_target_engine()
        
        # Test connections
        with source_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Source database (GCP) connection successful")
        
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Target database (Self-Hosted) connection successful")
        print()
        
        if dry_run:
            print("🔍 Would copy the following tables:")
            tables = get_table_list(source_engine)
            for table in tables:
                with source_engine.connect() as conn:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                print(f"   📋 {table}: {count:,} rows")
            print()
            print("✅ Dry run completed - no data was copied")
            return True
        
        # Get tables to copy
        tables = get_table_list(source_engine)
        print(f"📋 Found {len(tables)} tables to migrate")
        print()
        
        # Copy each table
        success_count = 0
        failed_tables = []
        for table in tables:
            if copy_table_data(source_engine, target_engine, table):
                success_count += 1
            else:
                failed_tables.append(table)
            print()
        
        print("=" * 60)
        print(f"✅ Migration completed!")
        print(f"📊 Successfully copied {success_count}/{len(tables)} tables")
        
        if failed_tables:
            print(f"⚠️  Failed tables: {', '.join(failed_tables)}")
        
        if success_count == len(tables):
            print("🎉 All data migrated successfully to self-hosted server!")
            return True
        else:
            print("⚠️  Some tables had errors - please review the output above")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Stop Cloud SQL Proxy
        if proxy_process:
            print("\n🔌 Stopping Cloud SQL Proxy...")
            proxy_process.terminate()
            proxy_process.wait()
            print("✅ Cloud SQL Proxy stopped")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate GCP production data to self-hosted server")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose SQL logging")
    
    args = parser.parse_args()
    
    if not args.dry_run:
        print("🚨 WARNING: This will copy ALL GCP production data to the self-hosted server!")
        print("🚨 This will OVERWRITE any existing data in the target database!")
        print()
        response = input("Are you sure you want to proceed? Type 'MIGRATE' to continue: ")
        if response != "MIGRATE":
            print("❌ Migration cancelled")
            return 1
    
    success = migrate_data(dry_run=args.dry_run, verbose=args.verbose)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

