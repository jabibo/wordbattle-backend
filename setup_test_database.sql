-- Setup Test Database Structure and Permissions
-- Run this script as postgres user on the Cloud SQL instance

-- Connect to production database first to get table structure
\c wordbattle_db;

-- Show current tables in production
\echo "=== PRODUCTION DATABASE TABLES ==="
\dt

-- Now connect to test database
\c wordbattle_test;

-- Check current state of test database
\echo "=== TEST DATABASE CURRENT STATE ==="
\dt

-- If tables don't exist, create them by copying from production
-- Note: This is a simplified approach - normally you'd use migrations

-- Grant full privileges to postgres user on test database
GRANT ALL PRIVILEGES ON DATABASE wordbattle_test TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO postgres;

-- Ensure postgres has creation privileges
ALTER USER postgres CREATEDB;
ALTER USER postgres CREATEROLE;

-- Check if we need to copy table structure
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public';
    
    IF table_count = 0 THEN
        RAISE NOTICE 'No tables found in wordbattle_test. Tables need to be created.';
        RAISE NOTICE 'This should be done via application startup or Alembic migrations.';
    ELSE
        RAISE NOTICE 'Found % tables in wordbattle_test database.', table_count;
    END IF;
END $$;

-- Show final state
\echo "=== TEST DATABASE FINAL STATE ==="
\dt
