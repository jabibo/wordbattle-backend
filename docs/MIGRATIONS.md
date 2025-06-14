# Database Migrations - Quick Reference

> ⚠️ **For comprehensive database documentation, see [DATABASE.md](./DATABASE.md)**

This is a quick reference for common migration operations. For detailed processes, troubleshooting, and best practices, refer to the comprehensive database documentation.

## Quick Commands

### Create New Migration
```bash
alembic revision --autogenerate -m "description of changes"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Check Current Version
```bash
alembic current
```

### Rollback Migration
```bash
alembic downgrade -1
```

## Common Scenarios

### Adding a New Column
1. Edit model in `app/models.py`
2. Generate migration: `alembic revision --autogenerate -m "Add new column"`
3. Review generated migration file
4. Test: `alembic upgrade head`

### Migration Troubleshooting
If you encounter migration issues:
1. Check current status: `alembic current`
2. For sync issues: Use `/admin/alembic/reset-to-current` endpoint
3. See [DATABASE.md](./DATABASE.md#troubleshooting) for detailed solutions

## Development Setup

### First-time Database Setup
```bash
# Create tables and load initial data
python -m app.database_manager init

# Load wordlists
python -m app.database_manager load
```

### Reset Development Database
```bash
python -m app.database_manager reset
# Type 'RESET' to confirm
```

## Production Notes

- Migrations run automatically on deployment
- Check `/admin/database/info` for status
- See [DATABASE.md](./DATABASE.md#production-deployment) for detailed deployment procedures

## Emergency Recovery

If migrations are broken:
```bash
# Use the Alembic reset endpoint (preserves data)
curl -X POST https://your-backend-url/admin/alembic/reset-to-current
```

For complete database recovery procedures, see [DATABASE.md](./DATABASE.md#recovery-procedures).