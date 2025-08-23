-- WordBattle Testing Database Complete Reset
-- ==========================================
-- This script completely resets the testing database to allow clean import

-- Drop all views
DROP VIEW IF EXISTS active_games CASCADE;
DROP VIEW IF EXISTS user_game_stats CASCADE;
DROP VIEW IF EXISTS game_summary CASCADE;

-- Drop all tables comprehensively
-- Use CASCADE to handle dependencies automatically

-- Additional specific table drops in case the above doesn't catch them all
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS user_stats CASCADE;
DROP TABLE IF EXISTS invitations CASCADE;
DROP TABLE IF EXISTS game_states CASCADE;
DROP TABLE IF EXISTS game_moves CASCADE;
DROP TABLE IF EXISTS game_participants CASCADE;
DROP TABLE IF EXISTS games CASCADE;
DROP TABLE IF EXISTS words CASCADE;
DROP TABLE IF EXISTS wordlists CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS game_invitations CASCADE;
DROP TABLE IF EXISTS moves CASCADE;

-- Drop all sequences
DROP SEQUENCE IF EXISTS users_id_seq CASCADE;
DROP SEQUENCE IF EXISTS games_id_seq CASCADE;
DROP SEQUENCE IF EXISTS wordlists_id_seq CASCADE;
DROP SEQUENCE IF EXISTS words_id_seq CASCADE;
DROP SEQUENCE IF EXISTS game_moves_id_seq CASCADE;
DROP SEQUENCE IF EXISTS user_stats_id_seq CASCADE;
DROP SEQUENCE IF EXISTS invitations_id_seq CASCADE;
DROP SEQUENCE IF EXISTS chat_messages_id_seq CASCADE;

-- Drop all custom types
-- First get all custom types and drop them
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    FOR r IN (SELECT typname FROM pg_type WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public') AND typtype = 'e') 
    LOOP
        EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
    END LOOP;
END $$;

-- Additional specific type drops in case the above doesn't catch them all
DROP TYPE IF EXISTS feedbackcategory CASCADE;
DROP TYPE IF EXISTS feedbackstatus CASCADE;
DROP TYPE IF EXISTS gamestatus CASCADE;
DROP TYPE IF EXISTS invitationstatus CASCADE;
DROP TYPE IF EXISTS userstatus CASCADE;
DROP TYPE IF EXISTS movetype CASCADE;
DROP TYPE IF EXISTS gamemode CASCADE;
DROP TYPE IF EXISTS language CASCADE;
DROP TYPE IF EXISTS difficulty CASCADE;

-- Drop all custom functions
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS generate_game_code() CASCADE;
DROP FUNCTION IF EXISTS calculate_user_stats() CASCADE;

-- Drop all indexes (they will be recreated with tables)
-- Note: Individual index drops are not needed as CASCADE will handle them

-- Drop all constraints (foreign keys, etc.)
-- Note: These will be dropped with the tables

-- The database is now completely clean and ready for import
-- (VACUUM skipped as it cannot run inside a transaction block)