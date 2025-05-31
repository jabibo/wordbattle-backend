#!/usr/bin/env python3
"""
Reset Production Database Script

This script connects to the AWS RDS production database and clears all game-related data.
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Production database connection
DB_HOST = "wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "Y3RHlw7BACKDFNg6QWmkirhPu"
DB_NAME = "wordbattle"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def reset_production_games():
    """Reset all game-related data in the production database."""
    print("🌐 Connecting to production database...")
    print(f"   Host: {DB_HOST}")
    print(f"   Database: {DB_NAME}")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("🗑️  Starting production database reset...")
        
        # Get counts before deletion
        print("\n📊 Current data counts:")
        tables_to_check = [
            ("chat_messages", "Chat Messages"),
            ("moves", "Moves"),
            ("players", "Players"),
            ("game_invitations", "Game Invitations"),
            ("games", "Games"),
            ("users", "Users"),
            ("wordlists", "WordLists")
        ]
        
        for table, name in tables_to_check:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   {name}: {count}")
            except Exception as e:
                print(f"   {name}: Error - {e}")
        
        print("\n🔄 Deleting game-related data...")
        
        # Delete in order to respect foreign key constraints
        delete_queries = [
            ("DELETE FROM chat_messages", "Chat Messages"),
            ("DELETE FROM moves", "Moves"),
            ("DELETE FROM players", "Players"),
            ("DELETE FROM game_invitations", "Game Invitations"),
            ("DELETE FROM games", "Games"),
        ]
        
        for query, name in delete_queries:
            try:
                result = db.execute(text(query))
                print(f"✅ Deleted {result.rowcount} {name}")
            except Exception as e:
                print(f"❌ Error deleting {name}: {e}")
        
        # Reset sequences
        print("\n🔄 Resetting sequences...")
        sequences = [
            "chat_messages_id_seq",
            "moves_id_seq", 
            "players_id_seq",
            "game_invitations_id_seq"
        ]
        
        for seq in sequences:
            try:
                db.execute(text(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1"))
                print(f"✅ Reset sequence: {seq}")
            except Exception as e:
                print(f"⚠️  Sequence {seq}: {e}")
        
        # Commit all changes
        db.commit()
        print("\n✅ Production database reset completed successfully!")
        
        # Show final counts
        print("\n📊 Final data counts:")
        for table, name in tables_to_check:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   {name}: {count}")
            except Exception as e:
                print(f"   {name}: Error - {e}")
        
    except Exception as e:
        print(f"❌ Error during reset: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def confirm_production_reset():
    """Ask for user confirmation before proceeding with production reset."""
    print("⚠️  WARNING: This will delete ALL game-related data from PRODUCTION!")
    print("   🌐 Target: AWS RDS Production Database")
    print(f"   🏠 Host: {DB_HOST}")
    print("   📊 Data to be deleted:")
    print("      - All games and their state")
    print("      - All player records")
    print("      - All moves history")
    print("      - All game invitations")
    print("      - All chat messages")
    print()
    print("✅ This will PRESERVE:")
    print("   - User accounts")
    print("   - WordLists")
    print()
    
    response = input("Are you ABSOLUTELY sure you want to proceed with PRODUCTION reset? (type 'RESET PRODUCTION' to confirm): ")
    return response == 'RESET PRODUCTION'

if __name__ == "__main__":
    print("🎮 WordBattle PRODUCTION Database Reset Tool")
    print("=" * 50)
    
    if confirm_production_reset():
        reset_production_games()
        print("\n🎉 Production reset complete! You can now start fresh games.")
    else:
        print("❌ Production reset cancelled.") 