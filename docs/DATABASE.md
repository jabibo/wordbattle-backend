# WordBattle Database Documentation

## Overview

WordBattle backend uses PostgreSQL as the primary database with SQLAlchemy ORM and Alembic for migrations. This document covers the complete database management lifecycle including schema changes, troubleshooting, and operational procedures.

## Database Schema

### Core Tables

#### Users (`users`)
- **id**: Primary key (integer, auto-increment)
- **username**: Unique username (string, max 50 characters)
- **email**: User email address (string, unique)
- **hashed_password**: Encrypted password (string)
- **is_active**: Account status (boolean, default true)
- **created_at**: Account creation timestamp
- **allow_invites**: Whether user accepts game invitations (boolean, default true)
- **preferred_languages**: User's preferred game languages (JSON array, default ["en", "de"])

#### Games (`games`)
- **id**: Primary key (integer, auto-increment)
- **player1_id**: Foreign key to users table
- **player2_id**: Foreign key to users table
- **status**: Game status (pending, active, completed, etc.)
- **language**: Game language (string)
- **current_turn**: Current player's turn
- **created_at**: Game creation timestamp
- **completed_at**: Game completion timestamp

#### Wordlists (`wordlists`)
- **id**: Primary key (integer, auto-increment)
- **word**: The word (string, indexed)
- **language**: Language code (string, e.g., "de", "en")
- **difficulty**: Word difficulty level (integer, 1-5)
- **category**: Word category (optional string)

#### Game Rounds (`game_rounds`)
- **id**: Primary key (integer, auto-increment)
- **game_id**: Foreign key to games table
- **round_number**: Round sequence number
- **word_id**: Foreign key to wordlists table
- **player1_guess**: Player 1's guess
- **player2_guess**: Player 2's guess
- **correct_answer**: The correct word
- **player1_points**: Points awarded to player 1
- **player2_points**: Points awarded to player 2

## Database Change Process

### 1. Development Workflow

#### Making Schema Changes

1. **Edit Model Files**
   ```python
   # In app/models.py
   class User(Base):
       __tablename__ = "users"
       # Add/modify columns here
       new_column = Column(String(100), nullable=True)
   ```

2. **Generate Migration**
   ```bash
   alembic revision --autogenerate -m "Add new_column to users table"
   ```

3. **Review Generated Migration**
   - Check `alembic/versions/xxxx_add_new_column.py`
   - Verify upgrade and downgrade functions
   - Add data migration logic if needed

4. **Test Migration Locally**
   ```bash
   alembic upgrade head
   ```

5. **Test Rollback**
   ```bash
   alembic downgrade -1
   alembic upgrade head
   ```

### 2. Production Deployment

#### Pre-deployment Checklist
- [ ] Migration tested locally
- [ ] Rollback procedure tested
- [ ] Data backup strategy confirmed
- [ ] Downtime window (if needed) scheduled
- [ ] Migration performs well on large datasets

#### Deployment Process
1. **Automatic Migration** (recommended)
   - Migrations run automatically on container startup
   - See `app/database_manager.py:run_migrations()`

2. **Manual Migration** (if needed)
   ```bash
   # In production container
   alembic upgrade head
   ```

#### Post-deployment Verification
- Check application logs for migration success
- Verify schema changes: `/admin/database/info`
- Test critical endpoints: `/debug/tokens`
- Monitor database performance

### 3. Migration Best Practices

#### Safe Migration Patterns
- **Additive changes**: Add columns with defaults, new tables
- **Backward compatible**: Don't drop columns/tables immediately
- **Phased approach**: Add → Deploy → Use → Remove old

#### Risky Operations
- **Column drops**: Can break running instances
- **Data type changes**: May require data conversion
- **Index changes**: Can lock tables
- **Large data migrations**: May timeout

#### Example Safe Migration
```python
def upgrade():
    # Add new column with default
    op.add_column('users', sa.Column('new_field', sa.String(50), 
                  nullable=False, server_default='default_value'))
    
    # Create index concurrently (PostgreSQL)
    op.create_index('ix_users_new_field', 'users', ['new_field'], 
                   postgresql_concurrently=True)

def downgrade():
    op.drop_index('ix_users_new_field')
    op.drop_column('users', 'new_field')
```

## Database Administration

### Environment Management

#### Development
- **SQLite**: Local development with `wordbattle.db`
- **PostgreSQL**: Local Docker setup
- **Seeding**: Use `python -m app.database_manager load` to populate wordlists

#### Testing
- **URL**: `postgresql://wordbattle:wordbattle123@/wordbattle_test`
- **Instance**: `wordbattle-1748668162:europe-west1:wordbattle-db`
- **Endpoint**: `https://wordbattle-backend-test-441752988736.europe-west1.run.app`

#### Production
- **URL**: TBD - to be configured when production environment is set up
- **Backup**: Automated daily backups
- **Monitoring**: Database performance metrics

### Common Operations

#### Check Database Status
```bash
# Via API
curl https://your-backend-url/admin/database/info

# Via CLI (in container)
python -m app.database_manager status
```

#### Load Wordlists
```bash
# Load German words (default)
python -m app.database_manager load

# Load English words
python -m app.database_manager load-en

# Load with limit
python -m app.database_manager load --limit 1000
```

#### Reset Database (Development Only)
```bash
python -m app.database_manager reset
# Type 'RESET' to confirm
```

## Troubleshooting

### Migration Issues

#### Problem: "Column does not exist" errors
**Symptoms**: 500 errors, SQLAlchemy column not found
**Causes**: 
- Migration not applied
- Migration failed partially
- Code expects columns that don't exist

**Solution**:
1. Check migration status: `alembic current`
2. Apply missing migrations: `alembic upgrade head`
3. If migrations are out of sync, use reset endpoint

#### Problem: Alembic version table out of sync
**Symptoms**: Migration commands fail, version conflicts
**Causes**:
- Database created outside Alembic
- Manual schema changes
- Failed migration recovery

**Solution**:
```bash
# Via API (preserves data)
curl -X POST https://your-backend-url/admin/alembic/reset-to-current

# Manual approach
alembic stamp head  # Mark current schema as latest
```

#### Problem: Migration timeout in production
**Symptoms**: Cloud Run deployment fails, long-running operations
**Causes**:
- Large table modifications
- Missing indexes
- Lock contention

**Solutions**:
- Split large migrations into smaller chunks
- Use `CONCURRENTLY` for index creation
- Schedule migrations during low-traffic periods
- Consider online schema change tools for very large tables

### Data Issues

#### Problem: Missing wordlist data
**Symptoms**: Empty word arrays, game creation fails
**Solution**:
```bash
python -m app.database_manager load --limit 10000
```

#### Problem: User authentication fails
**Symptoms**: Token validation errors, 401 responses
**Causes**: Missing user preference columns
**Solution**:
```bash
curl -X POST https://your-backend-url/admin/alembic/reset-to-current
```

### Performance Issues

#### Problem: Slow queries
**Diagnosis**:
- Enable PostgreSQL query logging
- Check for missing indexes
- Analyze query execution plans

**Solutions**:
- Add appropriate indexes
- Optimize query patterns
- Consider materialized views for complex aggregations

#### Problem: Connection pool exhaustion
**Symptoms**: "connection pool is at max size" errors
**Solutions**:
- Increase `pool_size` in database configuration
- Fix connection leaks in application code
- Add connection pooling monitoring

## Recovery Procedures

### Data Recovery

#### Backup Strategy
- **Automated**: Cloud SQL automated daily backups
- **Manual**: `pg_dump` for specific table exports
- **Point-in-time**: Cloud SQL provides PITR capability

#### Recovery Process
1. **Stop application** to prevent new writes
2. **Restore from backup** using Cloud SQL console
3. **Apply any missing migrations** if needed
4. **Restart application** and verify functionality

### Schema Recovery

#### If migrations are completely broken:
1. **Export data** from critical tables
2. **Reset Alembic state**: Drop `alembic_version` table
3. **Recreate schema** from models
4. **Reimport data**
5. **Stamp with current revision**

```bash
# Emergency schema reset (last resort)
python -c "
from app.database import engine, Base
from app.models import User, Game, WordList
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
"
alembic stamp head
```

## Development Guidelines

### Model Changes
- Always generate migrations for schema changes
- Include both upgrade and downgrade functions
- Test with realistic data volumes
- Consider backward compatibility

### Data Migrations
- Use raw SQL for complex data transformations
- Handle null values and edge cases
- Include progress logging for long operations
- Test rollback scenarios

### Testing
- Test migrations on copy of production data
- Verify application works after migration
- Test rollback procedures
- Include migration tests in CI/CD pipeline

## Monitoring and Maintenance

### Health Checks
- **API Health**: `/health` endpoint includes database status
- **Migration Status**: Check via `/admin/database/info`
- **Data Integrity**: Regular row counts and consistency checks

### Performance Monitoring
- Query execution times
- Connection pool usage
- Index effectiveness
- Slow query analysis

### Regular Maintenance
- **Vacuum/Analyze**: PostgreSQL maintenance (automated in Cloud SQL)
- **Index Maintenance**: Monitor and rebuild as needed
- **Statistics Update**: Ensure query planner has current stats
- **Backup Verification**: Regular restore testing

## Security Considerations

### Access Control
- Database user with minimal required permissions
- No direct database access from application servers
- Cloud SQL IAM authentication where possible

### Data Protection
- Encrypted connections (SSL/TLS)
- Encrypted at rest (Cloud SQL default)
- Personal data handling per GDPR requirements

### Audit Trail
- Migration history in `alembic_version` table
- Application logs for all database operations
- Cloud SQL audit logging enabled

## Emergency Contacts and Procedures

### Escalation Path
1. **Level 1**: Application developer
2. **Level 2**: Database administrator
3. **Level 3**: Cloud platform support

### Emergency Procedures
- **Data Loss**: Immediate backup restoration
- **Performance Issues**: Connection limiting and query analysis
- **Security Incident**: Immediate access revocation and audit

### Key Resources
- **Cloud SQL Console**: GCP Console → SQL
- **Monitoring**: Cloud Monitoring for database metrics
- **Logs**: Cloud Logging for application and database logs
- **Documentation**: This file and inline code comments 