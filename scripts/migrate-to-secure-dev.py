#!/usr/bin/env python3
"""
Migrate Data from Current Test Environment to Secure Development Environment

This script migrates data from:
  Source: wordbattle-1748668162:wordbattle_test 
  Target: wordbattle-secure:wordbattle_dev

Usage:
    python3 scripts/migrate-to-secure-dev.py [--dry-run] [--verbose]
"""

import os
import sys
import logging
import argparse
from typing import Dict, List
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker
from google.cloud.sql.connector import Connector

# Database configurations
SOURCE_CONFIG = {
    'project_id': 'wordbattle-1748668162',
    'region': 'europe-west1',
    'instance': 'wordbattle-db',
    'database': 'wordbattle_test',
    'user': 'wordbattle',
    'password': 'HKrzBR4nMpF4ddgf'  # Current password
}

TARGET_CONFIG = {
    'project_id': 'wordbattle-secure',
    'region': 'europe-west1', 
    'instance': 'wordbattle-db',
    'database': 'wordbattle_dev',
    'user': 'wordbattle_dev_app',
    'password': None  # Will be retrieved from secrets
}

# Tables to migrate in dependency order
MIGRATION_TABLES = [
    'users',
    'wordlists', 
    'games',
    'players',
    'moves',
    'game_invitations',
    'chat_messages',
    'feedback'
]

class SecureEnvironmentMigrator:
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.logger = self._setup_logging()
        self.source_engine = None
        self.target_engine = None
        self.connector = Connector()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('migration-to-secure.log')
            ]
        )
        return logging.getLogger(__name__)

    def _get_cloud_sql_connection(self, config: Dict) -> str:
        """Create Cloud SQL connection string."""
        instance_name = f"{config['project_id']}:{config['region']}:{config['instance']}"
        
        def getconn():
            return self.connector.connect(
                instance_name,
                "pg8000",
                user=config['user'],
                password=config['password'],
                db=config['database']
            )
        
        return create_engine("postgresql+pg8000://", creator=getconn)

    def _get_target_password(self) -> str:
        """Get target database password from Google Cloud Secret Manager."""
        import subprocess
        try:
            result = subprocess.run([
                'gcloud', 'secrets', 'versions', 'access', 'latest',
                '--secret=dev-db-password',
                '--project=wordbattle-secure'
            ], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get password from secrets: {e}")
            raise

    def connect_databases(self):
        """Connect to source and target databases."""
        self.logger.info("🔌 Connecting to databases...")
        
        # Connect to source (test environment)
        self.logger.info("   📊 Connecting to source: wordbattle-1748668162:wordbattle_test")
        self.source_engine = self._get_cloud_sql_connection(SOURCE_CONFIG)
        
        # Get target password and connect
        self.logger.info("   🔐 Getting secure environment credentials...")
        TARGET_CONFIG['password'] = self._get_target_password()
        
        self.logger.info("   🛡️  Connecting to target: wordbattle-secure:wordbattle_dev")
        self.target_engine = self._get_cloud_sql_connection(TARGET_CONFIG)
        
        # Test connections
        with self.source_engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user"))
            db, user = result.fetchone()
            self.logger.info(f"   ✅ Source connected: {db} as {user}")
            
        with self.target_engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user"))
            db, user = result.fetchone()
            self.logger.info(f"   ✅ Target connected: {db} as {user}")

    def get_table_stats(self, engine, table_name: str) -> int:
        """Get row count for a table."""
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()

    def migrate_table(self, table_name: str):
        """Migrate a single table from source to target."""
        self.logger.info(f"📊 Migrating table: {table_name}")
        
        # Get source data count
        source_count = self.get_table_stats(self.source_engine, table_name)
        self.logger.info(f"   📈 Source rows: {source_count}")
        
        if source_count == 0:
            self.logger.info(f"   ⏭️  Skipping empty table: {table_name}")
            return
            
        if self.dry_run:
            self.logger.info(f"   🔍 DRY RUN: Would migrate {source_count} rows")
            return

        # Clear target table
        with self.target_engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
            conn.commit()
            self.logger.info(f"   🗑️  Cleared target table")

        # Copy data
        with self.source_engine.connect() as source_conn:
            with self.target_engine.connect() as target_conn:
                # Get all data from source
                result = source_conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.fetchall()
                columns = result.keys()
                
                if rows:
                    # Prepare insert statement
                    column_list = ', '.join(columns)
                    placeholders = ', '.join([f':{col}' for col in columns])
                    insert_sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
                    
                    # Insert data
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        target_conn.execute(text(insert_sql), row_dict)
                    
                    target_conn.commit()
                    
        # Verify migration
        target_count = self.get_table_stats(self.target_engine, table_name)
        self.logger.info(f"   ✅ Migrated: {target_count} rows")
        
        if target_count != source_count:
            raise Exception(f"Migration failed: {source_count} source ≠ {target_count} target")

    def run_migration(self):
        """Run the complete migration process."""
        self.logger.info("🚀 Starting Migration to Secure Environment")
        self.logger.info("=" * 50)
        
        if self.dry_run:
            self.logger.info("🔍 DRY RUN MODE - No changes will be made")
        
        try:
            # Connect to databases
            self.connect_databases()
            
            # Migrate each table
            for table_name in MIGRATION_TABLES:
                try:
                    self.migrate_table(table_name)
                except Exception as e:
                    self.logger.error(f"❌ Failed to migrate {table_name}: {e}")
                    if not self.dry_run:
                        raise
            
            self.logger.info("🎉 Migration completed successfully!")
            self.logger.info(f"📊 Migrated {len(MIGRATION_TABLES)} tables to secure environment")
            
        except Exception as e:
            self.logger.error(f"❌ Migration failed: {e}")
            raise
        finally:
            # Close connections
            if self.source_engine:
                self.source_engine.dispose()
            if self.target_engine:
                self.target_engine.dispose()
            self.connector.close()

def main():
    parser = argparse.ArgumentParser(description='Migrate data to secure development environment')
    parser.add_argument('--dry-run', action='store_true', help='Preview migration without making changes')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    migrator = SecureEnvironmentMigrator(dry_run=args.dry_run, verbose=args.verbose)
    migrator.run_migration()

if __name__ == "__main__":
    main()
