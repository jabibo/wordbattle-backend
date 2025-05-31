-- Reset Games Database Script
-- This script clears all game-related data while preserving users and wordlists

-- Disable foreign key checks temporarily (PostgreSQL)
SET session_replication_role = replica;

-- Delete game-related data in order to respect foreign key constraints
DELETE FROM chat_messages;
DELETE FROM moves;
DELETE FROM players;
DELETE FROM game_invitations;
DELETE FROM games;

-- Re-enable foreign key checks
SET session_replication_role = DEFAULT;

-- Reset sequences (PostgreSQL)
ALTER SEQUENCE IF EXISTS chat_messages_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS moves_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS players_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS game_invitations_id_seq RESTART WITH 1;

-- Show remaining counts
SELECT 'Users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'WordLists' as table_name, COUNT(*) as count FROM wordlists
UNION ALL
SELECT 'Games' as table_name, COUNT(*) as count FROM games
UNION ALL
SELECT 'Players' as table_name, COUNT(*) as count FROM players
UNION ALL
SELECT 'Moves' as table_name, COUNT(*) as count FROM moves
UNION ALL
SELECT 'Game Invitations' as table_name, COUNT(*) as count FROM game_invitations
UNION ALL
SELECT 'Chat Messages' as table_name, COUNT(*) as count FROM chat_messages; 