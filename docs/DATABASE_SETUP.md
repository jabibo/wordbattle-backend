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
- **Status**: **PERMISSION ISSUE** - Tables exist but postgres user lacks access
- **Issue**: `permission denied for table users`
- **Solution**: Grant proper permissions via Google Cloud Console

#### 🔧 **IMMEDIATE FIX for Test Database Permissions:**

**Problem**: Test environment shows `permission denied for table users` errors.

**Quick Solution**:
1. Open [Google Cloud Console](https://console.cloud.google.com/sql/instances/wordbattle-db/overview?project=wordbattle-1748668162)
2. Click "Connect to this instance" → "Open Cloud Shell"  
3. Connect to `wordbattle_test` database as `postgres` user
4. Run these SQL commands:

```sql
-- Connect to test database
\c wordbattle_test;

-- Grant all privileges to postgres user
GRANT ALL PRIVILEGES ON DATABASE wordbattle_test TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO postgres;

-- Verify the fix
SELECT 'Permissions fixed!' as status;
\dt
```

5. Test the fix: `./test_fix.sh`

**Alternative**: Run `./scripts/fix-test-permissions-via-console.sh` for detailed instructions.

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

## ⚡ IMMEDIATE FIX: Test Database Permissions Issue

### THE PROPER SOLUTION: Alembic Migrations

**You're absolutely right!** The correct approach is to use Alembic migrations, not manual permission grants.

#### Why Alembic is the Right Solution:
- ✅ **Proper Database Management**: Alembic is designed for database schema management
- ✅ **Consistent Schema**: Ensures test and production databases have identical structure  
- ✅ **Version Control**: All database changes are tracked and versioned
- ✅ **Correct Ownership**: Tables created by Alembic have proper ownership automatically
- ✅ **Reproducible**: Same commands work across all environments

#### Current Alembic Setup:
```bash
# Check migration status
alembic current

# View migration history  
alembic history --verbose

# Apply all pending migrations
alembic upgrade head
```

#### The Challenge:
The issue is that Alembic needs to run **inside the Cloud Run environment** where:
1. Cloud SQL Proxy is available
2. Proper network access to the database exists
3. SSL connections work correctly

#### Three Approaches to Fix with Alembic:

### Approach 1: Add Migration Step to Deployment Script

**RECOMMENDED**: Modify `deploy-test.sh` to run Alembic migrations automatically:

```bash
# Add this to deploy-test.sh after the deployment
echo "Running Alembic migrations on test database..."
gcloud run services replace service-test.yaml --region=europe-west1

# Wait for deployment
sleep 30

# Run migrations via Cloud Run job
gcloud run jobs create alembic-migrate-test \
  --image=$IMAGE_URL \
  --task-timeout=600 \
  --set-env-vars="DATABASE_URL=postgresql://postgres:8G9kH2mP4vN1qR7sT6eW@/wordbattle_test?host=/cloudsql/wordbattle-1748668162:europe-west1:wordbattle-db&sslmode=require" \
  --add-cloudsql-instances=wordbattle-1748668162:europe-west1:wordbattle-db \
  --region=europe-west1 \
  --command=alembic \
  --args=upgrade,head

gcloud run jobs execute alembic-migrate-test --region=europe-west1 --wait
```

### Approach 2: Manual Migration via Cloud Run

Create a one-time job to run migrations:

```bash
# Create migration job
gcloud run jobs create test-db-migrate \
  --image=europe-west1-docker.pkg.dev/wordbattle-1748668162/wordbattle/backend:latest \
  --task-timeout=600 \
  --set-env-vars="DATABASE_URL=postgresql://postgres:8G9kH2mP4vN1qR7sT6eW@/wordbattle_test?host=/cloudsql/wordbattle-1748668162:europe-west1:wordbattle-db&sslmode=require" \
  --add-cloudsql-instances=wordbattle-1748668162:europe-west1:wordbattle-db \
  --region=europe-west1 \
  --command=alembic \
  --args=upgrade,head

# Execute the migration
gcloud run jobs execute test-db-migrate --region=europe-west1 --wait
```

### Approach 3: Interactive Container Session

Run an interactive session in Cloud Run to execute Alembic:

```bash
# Deploy first (to ensure image is available)
./deploy-test.sh

# Create interactive job
gcloud run jobs create test-db-shell \
  --image=europe-west1-docker.pkg.dev/wordbattle-1748668162/wordbattle/backend:latest \
  --task-timeout=600 \
  --set-env-vars="DATABASE_URL=postgresql://postgres:8G9kH2mP4vN1qR7sT6eW@/wordbattle_test?host=/cloudsql/wordbattle-1748668162:europe-west1:wordbattle-db&sslmode=require" \
  --add-cloudsql-instances=wordbattle-1748668162:europe-west1:wordbattle-db \
  --region=europe-west1 \
  --command=bash

# Execute interactive session  
gcloud run jobs execute test-db-shell --region=europe-west1 --wait

# Then inside the container:
# alembic current
# alembic upgrade head
```

#### Verification After Alembic Migration:

```bash
# Test the fix
curl -s "https://wordbattle-backend-test-441752988736.europe-west1.run.app/admin/database/admin-status"

# Should return proper JSON instead of permission errors
```

#### Future Database Changes:

Always use Alembic for schema changes:

```bash
# Create new migration
alembic revision --autogenerate -m "description of change"

# Review the generated migration file
# Apply to test first
alembic upgrade head

# Test thoroughly, then apply to production
```

---

## Legacy Fix (Manual Permissions) - NOT RECOMMENDED 