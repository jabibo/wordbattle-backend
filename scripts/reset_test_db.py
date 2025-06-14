#!/usr/bin/env python3
"""
Reset Test Database Script

This script connects to the GCP Cloud SQL test database and clears all game-related data.
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Test database connection (GCP Cloud SQL)
DB_HOST = "/cloudsql/wordbattle-1748668162:europe-west1:wordbattle-db"
DB_USER = "wordbattle"
DB_PASSWORD = "wordbattle123"
DB_NAME = "wordbattle_test"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?host={DB_HOST}"

def reset_test_games():
    """Reset all game-related data in the test database."""
    print("🧪 Connecting to test database...")
    print(f"   Instance: wordbattle-1748668162:europe-west1:wordbattle-db")
    print(f"   Database: {DB_NAME}")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("🗑️  Starting test database reset...")
        
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
            "game_invitations_id_seq",
            "games_id_seq"
        ]
        
        for seq in sequences:
            try:
                db.execute(text(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1"))
                print(f"✅ Reset sequence: {seq}")
            except Exception as e:
                print(f"⚠️  Sequence {seq}: {e}")
        
        # Commit all changes
        db.commit()
        print("\n✅ Test database reset completed successfully!")
        
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

def confirm_test_reset():
    """Ask for user confirmation before proceeding with test reset."""
    print("⚠️  WARNING: This will delete ALL game-related data from TEST database!")
    print("   🧪 Target: GCP Cloud SQL Test Database")
    print(f"   🏠 Instance: wordbattle-1748668162:europe-west1:wordbattle-db")
    print(f"   📊 Database: {DB_NAME}")
    print("   📊 Data to be deleted:")
    print("      - All games and their state")
    print("      - All player records")
    print("      - All moves history")
    print("      - All game invitations")
    print("      - All chat messages")
    print()
    print("✅ This will PRESERVE:")
    print("   - User accounts (player01, player02)")
    print("   - WordLists (110,000 German words)")
    print()
    
    response = input("Are you sure you want to reset the TEST database? (type 'RESET TEST' to confirm): ")
    return response == 'RESET TEST'

def reset_via_api():
    """Alternative method: Reset using the API endpoint."""
    import requests
    
    print("🌐 Alternative: Using API endpoint method...")
    try:
        # Use the admin endpoint we created
        url = "https://wordbattle-backend-test-441752988736.europe-west1.run.app/admin/database/reset-games"
        response = requests.post(url)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API reset successful!")
            print(f"   Message: {result.get('message', 'N/A')}")
            if 'deleted_counts' in result:
                print("   Deleted:")
                for table, count in result['deleted_counts'].items():
                    print(f"      {table}: {count}")
            return True
        else:
            print(f"❌ API reset failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API reset error: {e}")
        print("   Falling back to direct database method...")
        return False

if __name__ == "__main__":
    print("🎮 WordBattle TEST Database Reset Tool")
    print("=" * 50)
    
    if confirm_test_reset():
        # Try API method first, fallback to direct database
        if not reset_via_api():
            print("\n🔄 Using direct database connection...")
            reset_test_games()
        
        print("\n🎉 Test database reset complete! You can now start fresh games.")
    else:
        print("❌ Test database reset cancelled.") 