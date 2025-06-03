#!/usr/bin/env python3
"""
Reset Production Database Script

This script connects to the Google Cloud SQL production database and clears all game-related data.
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Production database connection (Google Cloud SQL)
DB_HOST = "35.187.90.105"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "Wordbattle2024"
DB_NAME = "wordbattle_db"

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
            ("friends", "Friends"),
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
        
        print("\n🔄 Using TRUNCATE CASCADE for faster reset...")
        
        # Use TRUNCATE CASCADE for faster deletion
        truncate_queries = [
            ("TRUNCATE TABLE chat_messages RESTART IDENTITY CASCADE", "Chat Messages"),
            ("TRUNCATE TABLE moves RESTART IDENTITY CASCADE", "Moves"),
            ("TRUNCATE TABLE players RESTART IDENTITY CASCADE", "Players"),
            ("TRUNCATE TABLE game_invitations RESTART IDENTITY CASCADE", "Game Invitations"),
            ("TRUNCATE TABLE games RESTART IDENTITY CASCADE", "Games"),
            ("TRUNCATE TABLE friends RESTART IDENTITY CASCADE", "Friends"),
        ]
        
        for query, name in truncate_queries:
            try:
                db.execute(text(query))
                print(f"✅ Truncated {name}")
                db.commit()  # Commit each truncate individually
            except Exception as e:
                print(f"❌ Error truncating {name}: {e}")
                db.rollback()
        
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
    print("   🌐 Target: Google Cloud SQL Production Database")
    print(f"   🏠 Host: {DB_HOST}")
    print("   📊 Data to be deleted:")
    print("      - All games and their state")
    print("      - All player records")
    print("      - All moves history")
    print("      - All game invitations")
    print("      - All chat messages")
    print("      - All friend relationships")
    print()
    print("✅ This will PRESERVE:")
    print("   - User accounts and their language preferences")
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