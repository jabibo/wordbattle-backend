# WordBattle Data Migration Guide

This guide provides instructions for migrating data from the insecure test environment to the secure production environment.

## Overview

The migration solution consists of two main components:

1. **Python Migration Script** (`scripts/migrate-data-test-to-prod.py`) - Core migration logic
2. **Shell Wrapper** (`scripts/migrate-data.sh`) - User-friendly interface with safety features

## Features

✅ **Automated Data Transfer** - Migrates all tables in correct dependency order  
✅ **Safety Checks** - Validates connections and data integrity  
✅ **Backup Support** - Creates backups before migration  
✅ **Dry Run Mode** - Preview changes without making modifications  
✅ **Rollback Capability** - Restore from backup if needed  
✅ **Selective Migration** - Migrate specific tables only  
✅ **Progress Monitoring** - Detailed logging and progress reporting  

## Prerequisites

### 1. Install Python Dependencies

```bash
cd wordbattle-backend
pip install -r scripts/requirements-migration.txt
```

### 2. Verify Environment Files

Ensure both environment files exist and are configured correctly:

- `deploy.testing.env` - Test database configuration
- `deploy.production.env` - Production database configuration

### 3. Database Access

Make sure you have:
- Network access to both databases
- Valid credentials for both environments
- Appropriate permissions for data operations

## Quick Start

### 1. Check Prerequisites

```bash
./scripts/migrate-data.sh check
```

### 2. Preview Migration (Dry Run)

```bash
./scripts/migrate-data.sh preview
```

### 3. Create Backup

```bash
./scripts/migrate-data.sh backup
```

### 4. Run Migration

```bash
./scripts/migrate-data.sh migrate
```

### 5. Verify Results

```bash
./scripts/migrate-data.sh verify
```

## Advanced Usage

### Migrate Specific Tables

```bash
# Migrate only users and games tables
./scripts/migrate-data.sh migrate users,games

# Using Python script directly
python3 scripts/migrate-data-test-to-prod.py --tables users,games --verbose
```

### Force Migration (Skip Prompts)

```bash
./scripts/migrate-data.sh migrate --force
```

### Detailed Logging

```bash
python3 scripts/migrate-data-test-to-prod.py --verbose
```

## Migration Tables

The following tables are migrated in dependency order:

1. `users` - Base user accounts
2. `user_profiles` - User preferences and settings  
3. `wordlists` - Dictionary data
4. `words` - Word entries
5. `games` - Game instances
6. `game_participants` - Players in games
7. `game_moves` - Individual moves
8. `game_states` - Current game states
9. `invitations` - Game invitations
10. `user_stats` - User statistics
11. `chat_messages` - Game chat history

## Safety Features

### Automatic Backups

Before each migration, the script can automatically create a backup of the production database:

```bash
# Manual backup
./scripts/migrate-data.sh backup

# Automatic backup during migration
./scripts/migrate-data.sh migrate  # Will prompt for backup
```

### Data Validation

After migration, the script validates:
- Row counts match between source and destination
- Primary key constraints are maintained
- Data integrity is preserved

### Rollback Support

If something goes wrong, you can rollback to the last backup:

```bash
./scripts/migrate-data.sh rollback
```

## Troubleshooting

### Connection Issues

If you encounter database connection errors:

1. Check environment files have correct credentials
2. Verify network connectivity to databases
3. Ensure Cloud SQL proxy is running if needed
4. Check firewall rules and IP allowlists

### Migration Failures

If migration fails partway through:

1. Check the logs for specific error messages
2. Verify data types and constraints match between databases
3. Use selective migration to test individual tables
4. Consider running with `--dry-run` first

### Performance Issues

For large datasets:

1. Run migration during low-traffic periods
2. Consider migrating tables individually
3. Monitor database performance during migration
4. Use Cloud SQL insights to track progress

## Example Migration Workflow

```bash
# 1. Check everything is ready
./scripts/migrate-data.sh check

# 2. See what will be migrated
./scripts/migrate-data.sh preview

# 3. Create a safety backup
./scripts/migrate-data.sh backup

# 4. Run the migration
./scripts/migrate-data.sh migrate

# 5. Verify everything worked
./scripts/migrate-data.sh verify

# 6. If issues, rollback
# ./scripts/migrate-data.sh rollback
```

## Security Considerations

- Environment files contain sensitive database credentials
- Backups may contain sensitive user data
- Run migrations from secure, trusted environments
- Clean up temporary files after migration
- Review access logs after migration

## Monitoring

The migration provides detailed logging including:

- Connection status and validation
- Table-by-table progress
- Row counts and data statistics
- Error messages and warnings
- Migration duration and performance metrics

## Post-Migration

After successful migration:

1. Update application configuration to use production database
2. Test application functionality thoroughly
3. Monitor application performance and error rates
4. Clean up test environment if no longer needed
5. Document the migration for future reference

## Script Reference

### migrate-data.sh Commands

- `check` - Verify prerequisites and configuration
- `preview` - Show migration preview (dry run)
- `backup` - Create production database backup
- `migrate` - Run the migration
- `verify` - Verify migration results
- `rollback` - Restore from last backup

### Python Script Options

- `--dry-run` - Preview mode, no changes made
- `--verbose` - Detailed logging output
- `--force` - Skip confirmation prompts
- `--tables TABLE1,TABLE2` - Migrate specific tables only

## Support

If you encounter issues:

1. Check the logs for detailed error messages
2. Review this documentation for troubleshooting steps
3. Verify database connectivity and permissions
4. Test with dry-run mode first
5. Consider selective table migration for debugging