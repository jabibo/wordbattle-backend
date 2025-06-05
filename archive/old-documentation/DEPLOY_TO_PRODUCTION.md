# Deploy Language Field to Production

## 🚀 Production Deployment Commands

### On your production server, run these commands:

```bash
# 1. SSH into your production server
ssh your-production-server

# 2. Navigate to the backend directory
cd /path/to/wordbattle-backend

# 3. Pull the latest changes
git pull origin production

# 4. Restart the services (this will run the migration automatically)
docker-compose down
docker-compose up -d

# 5. Check the logs to verify migration ran
docker-compose logs app | grep -i migration

# 6. Verify the language field exists
docker-compose exec db psql -U postgres -d wordbattle -c "\d users"
```

## ✅ What to expect:

You should see logs like:
```
INFO:app.main:Running database migrations...
INFO:migrations.add_user_language_field:Starting migration: Adding language field to users table
INFO:migrations.add_user_language_field:Migration completed successfully: Added language column
INFO:app.main:Database migrations completed successfully
```

## 🔍 Verify deployment:

```bash
# Test the language endpoints
curl -H "Authorization: Bearer YOUR_TOKEN" https://your-production-url/users/language

# Should return: {"language": "en", "available_languages": ["en", "de", "fr", "es", "it"]}
```

## 🆘 If migration fails:

Run manual SQL:
```bash
docker-compose exec db psql -U postgres -d wordbattle -c "ALTER TABLE users ADD COLUMN language VARCHAR DEFAULT 'en';"
``` 