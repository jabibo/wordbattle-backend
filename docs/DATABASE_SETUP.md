# Database Setup Guide

This guide covers setting up and configuring the databases for WordBattle backend.

## 🗄️ Database Architecture

### Cloud SQL Instance
- **Instance**: `wordbattle-db`
- **Engine**: PostgreSQL
- **Databases**:
  - `wordbattle_db` (Production)
  - `wordbattle_test` (Test)

### Environment Separation
- **Production**: Uses `wordbattle_db` database
- **Test**: Uses `wordbattle_test` database
- **Same Instance**: Both environments share the Cloud SQL instance for cost efficiency

## 🚀 Initial Setup

### 1. Production Database (Already Configured)
The production database is fully configured with:
- ✅ All tables created
- ✅ Proper permissions set
- ✅ Wordlists imported (~780k words)
- ✅ Admin user support

### 2. Test Database Setup Required

The test database needs initial setup:

#### Option A: Copy Structure from Production
```sql
-- Connect to Cloud SQL as superuser
-- Create tables in wordbattle_test by copying structure
CREATE TABLE wordbattle_test.users (LIKE wordbattle_db.users INCLUDING ALL);
CREATE TABLE wordbattle_test.wordlists (LIKE wordbattle_db.wordlists INCLUDING ALL);
-- ... copy all other tables

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE wordbattle_test TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

#### Option B: Run Migrations
```bash
# Set test database URL and run migrations
export DATABASE_URL="postgresql://postgres:password@/wordbattle_test?host=/cloudsql/instance"
alembic upgrade head
```

#### Option C: Import Test Data
```bash
# Deploy to test environment (will create tables automatically via FastAPI)
./deploy-test.sh

# Import wordlists to test environment
curl -X POST "https://wordbattle-backend-test-441752988736.europe-west1.run.app/admin/database/import-wordlists"

# Create admin user
curl -X POST "https://wordbattle-backend-test-441752988736.europe-west1.run.app/admin/database/create-default-admin"
```

## 🔧 Current Status

### Production Environment ✅
- **Database**: `wordbattle_db` 
- **Status**: Fully functional
- **Admin User**: `jan@binge.de` exists
- **Wordlists**: ~780,256 words imported
- **Health**: All endpoints working

### Test Environment ⚠️
- **Database**: `wordbattle_test`
- **Status**: Needs permissions setup
- **Issue**: Tables exist but postgres user lacks permissions
- **Solution**: Run database initialization script

## 🛠️ Fixing Test Environment

### Quick Fix (Recommended)
Since both environments should work independently, run this command to use the production database structure for the test environment temporarily:

1. **Update test deployment** to use a separate database user with proper permissions, or
2. **Copy production structure** to test database, or  
3. **Use production database for now** and separate later when needed

### Manual Database Setup
```sql
-- Connect to Cloud SQL as superuser
\c wordbattle_test;

-- Grant all privileges to postgres user
GRANT ALL PRIVILEGES ON DATABASE wordbattle_test TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO postgres;

-- Ensure postgres user has creation privileges
ALTER USER postgres CREATEDB;
ALTER USER postgres CREATEROLE;
```

## 📊 Database Monitoring

### Health Checks
```bash
# Production database health
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/admin/database/admin-status

# Test database health  
curl https://wordbattle-backend-test-441752988736.europe-west1.run.app/admin/database/admin-status

# Wordlist status
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/admin/database/wordlist-status
```

### Common Database Operations
```bash
# Import wordlists
curl -X POST "https://your-domain.com/admin/database/import-wordlists"

# Create admin user
curl -X POST "https://your-domain.com/admin/database/create-default-admin"

# Reset game data (safe)
curl -X POST "https://your-domain.com/admin/database/reset-games" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 🔐 Security Considerations

### Database Credentials
- **Production**: Uses environment-specific password
- **Test**: Should use same credentials for simplicity (data is isolated)
- **Access**: Controlled via Cloud SQL IAM and network policies

### Data Isolation
- **Separate Databases**: Ensures test data doesn't affect production
- **Same Instance**: Cost-effective while maintaining isolation
- **Reset Safety**: Test environment can be reset without affecting production

## 🚨 Troubleshooting

### Permission Denied Errors
```
Error: permission denied for table users
```
**Solution**: Run the database initialization script or grant proper permissions to postgres user.

### Connection Errors
```
Error: could not translate host name "db" to address
```
**Solution**: Ensure Cloud SQL proxy configuration is correct in deployment scripts.

### Table Not Found Errors
```
Error: relation "users" does not exist
```
**Solution**: Run Alembic migrations or copy table structure from production database.

---

## 📝 Next Steps

1. **Set up test database permissions** using one of the methods above
2. **Verify test environment** functionality with admin endpoints
3. **Import test wordlists** if needed for testing
4. **Document the chosen setup method** for future reference

Once the test database is properly configured, both environments will work independently with full functionality. 