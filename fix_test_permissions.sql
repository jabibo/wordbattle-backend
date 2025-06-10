-- Connect to the test database
\c wordbattle_test;

-- Check current permissions
\echo "Current database and user:"
SELECT current_database(), current_user;

-- Check if tables exist
\echo "Checking if tables exist:"
SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public';

-- Grant all privileges on the test database to postgres user
\echo "Granting database privileges..."
GRANT ALL PRIVILEGES ON DATABASE wordbattle_test TO postgres;

-- Grant privileges on the public schema
\echo "Granting schema privileges..."
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;

-- Grant privileges on all existing tables
\echo "Granting table privileges..."
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;

-- Grant privileges on all existing sequences
\echo "Granting sequence privileges..."
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Set default privileges for future tables
\echo "Setting default privileges..."
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO postgres;

-- Ensure postgres can create tables
\echo "Ensuring postgres can create objects..."
ALTER USER postgres CREATEDB;

-- If tables don't exist, we may need to create them
-- Check if users table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users' AND table_schema = 'public') THEN
        RAISE NOTICE 'Tables do not exist in wordbattle_test. They will be created automatically when the application starts.';
    ELSE
        RAISE NOTICE 'Tables exist. Permissions have been granted.';
    END IF;
END $$;

-- Verify permissions
\echo "Verifying permissions:"
SELECT 
    schemaname,
    tablename,
    has_table_privilege('postgres', schemaname||'.'||tablename, 'SELECT') as can_select,
    has_table_privilege('postgres', schemaname||'.'||tablename, 'INSERT') as can_insert,
    has_table_privilege('postgres', schemaname||'.'||tablename, 'UPDATE') as can_update,
    has_table_privilege('postgres', schemaname||'.'||tablename, 'DELETE') as can_delete
FROM pg_tables 
WHERE schemaname = 'public'
LIMIT 5;

\echo "Test database permissions fixed!"
