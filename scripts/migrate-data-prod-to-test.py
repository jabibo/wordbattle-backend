#!/usr/bin/env python3
"""
WordBattle Data Migration Script - Production to Testing
========================================================

Automated solution to migrate all data from production environment to testing/dev.

This script handles:
- User accounts and profiles
- Games and game states  
- Word dictionaries
- All game history and moves
- User preferences and settings
- Data integrity validation

Usage:
    python migrate-data-prod-to-test.py [--dry-run] [--verbose] [--force]
    
Options:
    --dry-run    Show what would be migrated without making changes
    --verbose    Show detailed progress information
    --force      Skip confirmation prompts
    --tables     Comma-separated list of specific tables to migrate
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Add the app directory to the path to import our models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from dotenv import load_dotenv

class DatabaseMigrator:
    """Handles secure data migration between production and testing databases."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.logger = self._setup_logging()
        
        # Database connections
        self.prod_conn = None
        self.test_conn = None
        
        # Migration statistics
        self.stats = {
            'tables_migrated': 0,
            'rows_migrated': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
        
        # Tables to migrate in dependency order
        self.migration_tables = [
            'users',           # Base user accounts
            'user_profiles',   # User preferences and settings
            'wordlists',       # Dictionary data
            'words',           # Word entries
            'games',           # Game instances
            'game_participants', # Players in games
            'game_moves',      # Individual moves
            'game_states',     # Current game states
            'invitations',     # Game invitations
            'user_stats',      # User statistics
            'chat_messages',   # Game chat history
        ]
    
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for the migration process."""
        logger = logging.getLogger('migration')
        
        # Set level based on verbosity
        level = logging.DEBUG if self.verbose else logging.INFO
        logger.setLevel(level)
        
        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def _load_environment_config(self, env_file: str) -> Dict[str, str]:
        """Load database configuration from environment file."""
        env_path = os.path.join(os.path.dirname(__file__), '..', env_file)
        
        if not os.path.exists(env_path):
            raise FileNotFoundError(f"Environment file not found: {env_path}")
        
        # Load the .env file
        load_dotenv(env_path)
        
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'cloud_sql_instance': os.getenv('CLOUD_SQL_INSTANCE_NAME'),
        }
        
        # Validate required fields
        required_fields = ['database', 'user', 'password']
        missing_fields = [field for field in required_fields if not config[field]]
        
        if missing_fields:
            raise ValueError(f"Missing required database config: {missing_fields}")
        
        return config
    
    def connect_databases(self):
        """Establish connections to both production and testing databases."""
        self.logger.info("🔗 Connecting to databases...")
        
        try:
            # Load production database config (SOURCE)
            prod_config = self._load_environment_config('deploy.production.env')
            self.logger.debug(f"Production DB (SOURCE): {prod_config['database']} on {prod_config['host']}")
            
            # Load testing database config (DESTINATION)
            test_config = self._load_environment_config('deploy.testing.env')
            self.logger.debug(f"Testing DB (DESTINATION): {test_config['database']} on {test_config['host']}")
            
            # Connect to production database (SOURCE)
            self.prod_conn = psycopg2.connect(
                host=prod_config['host'],
                port=prod_config['port'],
                database=prod_config['database'],
                user=prod_config['user'],
                password=prod_config['password']
            )
            
            # Connect to testing database (DESTINATION)
            self.test_conn = psycopg2.connect(
                host=test_config['host'],
                port=test_config['port'],
                database=test_config['database'],
                user=test_config['user'],
                password=test_config['password']
            )
            
            self.logger.info("✅ Database connections established")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to databases: {e}")
            raise
    
    def validate_connections(self):
        """Validate that both database connections are working."""
        self.logger.info("🔍 Validating database connections...")
        
        try:
            # Test production database
            with self.prod_conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                prod_version = cursor.fetchone()[0]
                self.logger.debug(f"Production DB version: {prod_version}")
            
            # Test testing database
            with self.test_conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                test_version = cursor.fetchone()[0]
                self.logger.debug(f"Testing DB version: {test_version}")
            
            self.logger.info("✅ Database connections validated")
            
        except Exception as e:
            self.logger.error(f"❌ Database validation failed: {e}")
            raise
    
    def get_table_info(self, conn, table_name: str) -> Dict[str, Any]:
        """Get information about a table structure and data count."""
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()['count']
            
            # Get primary key columns
            cursor.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tco
                JOIN information_schema.key_column_usage kcu 
                    ON kcu.constraint_name = tco.constraint_name
                WHERE tco.constraint_type = 'PRIMARY KEY' 
                AND tco.table_name = %s;
            """, (table_name,))
            pk_columns = [row['column_name'] for row in cursor.fetchall()]
            
            return {
                'columns': columns,
                'row_count': row_count,
                'primary_keys': pk_columns
            }
    
    def table_exists(self, conn, table_name: str) -> bool:
        """Check if a table exists in the database."""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_name,))
            return cursor.fetchone()[0]
    
    def migrate_table(self, table_name: str) -> bool:
        """Migrate a single table from production to testing."""
        self.logger.info(f"📊 Migrating table: {table_name}")
        
        try:
            # Check if table exists in both databases
            if not self.table_exists(self.prod_conn, table_name):
                self.logger.warning(f"⚠️  Table {table_name} does not exist in production database, skipping")
                return True
            
            if not self.table_exists(self.test_conn, table_name):
                self.logger.warning(f"⚠️  Table {table_name} does not exist in testing database, skipping")
                return True
            
            # Get table information
            prod_info = self.get_table_info(self.prod_conn, table_name)
            test_info = self.get_table_info(self.test_conn, table_name)
            
            self.logger.debug(f"Production {table_name}: {prod_info['row_count']} rows")
            self.logger.debug(f"Testing {table_name}: {test_info['row_count']} rows")
            
            # If no data in production table, skip
            if prod_info['row_count'] == 0:
                self.logger.info(f"ℹ️  Table {table_name} is empty in production database, skipping")
                return True
            
            # Get all data from production table
            with self.prod_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(f"SELECT * FROM {table_name};")
                rows = cursor.fetchall()
            
            if self.dry_run:
                self.logger.info(f"🧪 DRY RUN: Would migrate {len(rows)} rows from {table_name}")
                return True
            
            # Clear testing table (careful!)
            with self.test_conn.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")
                self.logger.debug(f"Cleared testing table {table_name}")
            
            # Insert data into testing table
            if rows:
                columns = list(rows[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                with self.test_conn.cursor() as cursor:
                    for row in rows:
                        values = [row[col] for col in columns]
                        cursor.execute(insert_sql, values)
                
                # Commit the transaction
                self.test_conn.commit()
                
                self.logger.info(f"✅ Migrated {len(rows)} rows to {table_name}")
                self.stats['rows_migrated'] += len(rows)
            
            self.stats['tables_migrated'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to migrate table {table_name}: {e}")
            self.stats['errors'] += 1
            
            # Rollback on error
            if not self.dry_run:
                self.test_conn.rollback()
            
            return False
    
    def validate_migration(self) -> bool:
        """Validate that the migration was successful."""
        self.logger.info("🔍 Validating migration results...")
        
        validation_passed = True
        
        for table_name in self.migration_tables:
            if not self.table_exists(self.prod_conn, table_name):
                continue
                
            try:
                prod_info = self.get_table_info(self.prod_conn, table_name)
                test_info = self.get_table_info(self.test_conn, table_name)
                
                if prod_info['row_count'] != test_info['row_count']:
                    self.logger.error(
                        f"❌ Row count mismatch in {table_name}: "
                        f"production={prod_info['row_count']}, testing={test_info['row_count']}"
                    )
                    validation_passed = False
                else:
                    self.logger.debug(f"✅ {table_name}: {test_info['row_count']} rows migrated correctly")
                    
            except Exception as e:
                self.logger.error(f"❌ Validation failed for {table_name}: {e}")
                validation_passed = False
        
        if validation_passed:
            self.logger.info("✅ Migration validation passed")
        else:
            self.logger.error("❌ Migration validation failed")
        
        return validation_passed
    
    def run_migration(self, specific_tables: Optional[List[str]] = None):
        """Run the complete migration process."""
        self.logger.info("🚀 Starting WordBattle data migration (Production → Testing)")
        self.logger.info(f"📅 Migration started at: {self.stats['start_time']}")
        
        if self.dry_run:
            self.logger.info("🧪 Running in DRY RUN mode - no changes will be made")
        
        try:
            # Connect to databases
            self.connect_databases()
            self.validate_connections()
            
            # Determine which tables to migrate
            tables_to_migrate = specific_tables or self.migration_tables
            
            self.logger.info(f"📋 Tables to migrate: {', '.join(tables_to_migrate)}")
            
            # Migrate each table
            success_count = 0
            for table_name in tables_to_migrate:
                if self.migrate_table(table_name):
                    success_count += 1
            
            # Validate migration if not dry run
            if not self.dry_run:
                validation_passed = self.validate_migration()
                if not validation_passed:
                    self.logger.error("❌ Migration validation failed - please review the logs")
                    return False
            
            # Print summary
            self.stats['end_time'] = datetime.now()
            duration = self.stats['end_time'] - self.stats['start_time']
            
            self.logger.info("🎉 Migration completed successfully!")
            self.logger.info(f"📊 Summary:")
            self.logger.info(f"   - Tables processed: {len(tables_to_migrate)}")
            self.logger.info(f"   - Tables migrated: {self.stats['tables_migrated']}")
            self.logger.info(f"   - Rows migrated: {self.stats['rows_migrated']}")
            self.logger.info(f"   - Errors: {self.stats['errors']}")
            self.logger.info(f"   - Duration: {duration}")
            
            return self.stats['errors'] == 0
            
        except Exception as e:
            self.logger.error(f"❌ Migration failed: {e}")
            return False
        
        finally:
            # Close connections
            if self.prod_conn:
                self.prod_conn.close()
            if self.test_conn:
                self.test_conn.close()

def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate WordBattle data from production to testing environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate-data-prod-to-test.py --dry-run --verbose
  python migrate-data-prod-to-test.py --force
  python migrate-data-prod-to-test.py --tables users,games --verbose
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress information'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    parser.add_argument(
        '--tables',
        type=str,
        help='Comma-separated list of specific tables to migrate'
    )
    
    args = parser.parse_args()
    
    # Parse specific tables if provided
    specific_tables = None
    if args.tables:
        specific_tables = [table.strip() for table in args.tables.split(',')]
    
    # Confirmation prompt (unless --force is used)
    if not args.force and not args.dry_run:
        print("⚠️  WARNING: This will overwrite ALL data in the testing database!")
        print("   This will copy production data to your secure dev/testing database.")
        print("   Make sure you have a backup if needed.")
        print()
        response = input("Are you sure you want to continue? (type 'yes' to confirm): ")
        
        if response.lower() != 'yes':
            print("❌ Migration cancelled")
            return 1
    
    # Create migrator and run migration
    migrator = DatabaseMigrator(dry_run=args.dry_run, verbose=args.verbose)
    success = migrator.run_migration(specific_tables)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())