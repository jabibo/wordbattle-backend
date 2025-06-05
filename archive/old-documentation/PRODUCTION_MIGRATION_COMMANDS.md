# Production Migration Commands

## SSH into Production Server
```bash
ssh your-production-server

# Navigate to backend directory
cd /path/to/wordbattle-backend

# Pull latest changes (if not done already)
git pull origin production

# Run the migration
python migrations/add_user_language_field.py
```

## Alternative: Run migration inside Docker container
```bash
# If using Docker on production
docker-compose exec app python migrations/add_user_language_field.py
```

## Verify migration success
```bash
# Connect to PostgreSQL and check the schema
docker-compose exec db psql -U postgres -d wordbattle -c "\d users"

# Should show the 'language' column
```

## Manual SQL if migration script fails
```sql
-- Connect to production database and run:
ALTER TABLE users ADD COLUMN language VARCHAR DEFAULT 'en';
UPDATE users SET language = 'en' WHERE language IS NULL;
``` 