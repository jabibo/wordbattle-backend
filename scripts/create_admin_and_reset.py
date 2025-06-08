#!/usr/bin/env python3
"""
Create Admin User and Reset Production Database Script

This script connects directly to the GCP Cloud SQL production database to:
1. Create an admin user if it doesn't exist
2. Reset all game-related data
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from datetime import datetime, timezone

# Production database connection (GCP Cloud SQL)
DB_HOST = "/cloudsql/wordbattle-1748668162:europe-west1:wordbattle-db"
DB_USER = "wordbattle"
DB_PASSWORD = "wordbattle123"
DB_NAME = "wordbattle_db"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?host={DB_HOST}"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user(db):
    """Create an admin user if it doesn't exist."""
    admin_email = "jan@binge.de"
    admin_username = "janadmin"
    
    # Check if admin user already exists
    result = db.execute(text("SELECT id, username, email, is_admin FROM users WHERE email = :email"), 
                       {"email": admin_email})
    existing_user = result.fetchone()
    
    if existing_user:
        if existing_user.is_admin:
            print(f"✅ Admin user already exists: {existing_user.username} ({existing_user.email})")
            return existing_user.id
        else:
            # Make existing user admin
            db.execute(text("UPDATE users SET is_admin = true WHERE email = :email"), 
                      {"email": admin_email})
            db.commit()
            print(f"✅ Made existing user admin: {existing_user.username} ({existing_user.email})")
            return existing_user.id
    else:
        # Create new admin user
        hashed_password = pwd_context.hash("admin123")
        now = datetime.now(timezone.utc)
        
        result = db.execute(text("""
            INSERT INTO users (username, email, hashed_password, is_admin, is_email_verified, created_at)
            VALUES (:username, :email, :hashed_password, true, true, :created_at)
            RETURNING id
        """), {
            "username": admin_username,
            "email": admin_email,
            "hashed_password": hashed_password,
            "created_at": now
        })
        
        user_id = result.scalar()
        db.commit()
        print(f"✅ Created new admin user: {admin_username} ({admin_email}) with password 'admin123'")
        return user_id

def reset_production_games(db):
    """Reset all game-related data in the production database."""
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
    
    before_counts = {}
    for table, name in tables_to_check:
        try:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            before_counts[name] = count
            print(f"   {name}: {count}")
        except Exception as e:
            print(f"   {name}: Error - {e}")
            before_counts[name] = 0
    
    print("\n🔄 Deleting game-related data...")
    
    # Delete in order to respect foreign key constraints
    delete_queries = [
        ("DELETE FROM chat_messages", "Chat Messages"),
        ("DELETE FROM moves", "Moves"),
        ("DELETE FROM players", "Players"),
        ("DELETE FROM game_invitations", "Game Invitations"),
        ("DELETE FROM games", "Games"),
        ("DELETE FROM users", "Users"),
    ]
    
    deleted_counts = {}
    for query, name in delete_queries:
        try:
            result = db.execute(text(query))
            count = result.rowcount
            deleted_counts[name] = count
            print(f"✅ Deleted {count} {name}")
        except Exception as e:
            print(f"❌ Error deleting {name}: {e}")
            deleted_counts[name] = 0
    
    # Reset sequences
    print("\n🔄 Resetting sequences...")
    sequences = [
        "chat_messages_id_seq",
        "moves_id_seq", 
        "players_id_seq",
        "game_invitations_id_seq",
        "users_id_seq"
    ]
    
    reset_sequences = []
    for seq in sequences:
        try:
            db.execute(text(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1"))
            reset_sequences.append(seq)
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
    
    return before_counts, deleted_counts, reset_sequences

def confirm_production_reset():
    """Ask for user confirmation before proceeding with production reset."""
    print("⚠️  WARNING: This will delete ALL game-related data from PRODUCTION!")
    print("   🌐 Target: GCP Cloud SQL Production Database")
    print(f"   🏠 Instance: wordbattle-1748668162:europe-west1:wordbattle-db")
    print(f"   📋 Database: {DB_NAME}")
    print("   📊 Data to be deleted:")
    print("      - ALL USER ACCOUNTS")
    print("      - All games and their state")
    print("      - All player records")
    print("      - All moves history")
    print("      - All game invitations")
    print("      - All chat messages")
    print()
    print("✅ This will PRESERVE:")
    print("   - WordLists ONLY (110,000 German words)")
    print()
    print("📝 This will also:")
    print("   - Create a new admin user (jan@binge.de) after deletion")
    print()
    
    response = input("Are you ABSOLUTELY sure you want to proceed with PRODUCTION reset? (type 'RESET PRODUCTION' to confirm): ")
    return response == 'RESET PRODUCTION'

def main():
    print("🎮 WordBattle PRODUCTION Database Management Tool")
    print("=" * 60)
    
    if not confirm_production_reset():
        print("❌ Production reset cancelled.")
        return
    
    print("🌐 Connecting to production database...")
    print(f"   Instance: wordbattle-1748668162:europe-west1:wordbattle-db")
    print(f"   Database: {DB_NAME}")
    
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        print(f"\n🗑️  Proceeding with FULL reset (users + games)...")
        before_counts, deleted_counts, reset_sequences = reset_production_games(db)
        
        print("\n👤 Creating new admin user...")
        admin_user_id = create_admin_user(db)
        
        print("\n🎉 Production reset complete!")
        print(f"   👤 Admin user ID: {admin_user_id}")
        print(f"   📊 Total items deleted: {sum(deleted_counts.values())}")
        print(f"   🔄 Sequences reset: {len(reset_sequences)}")
        print("\n📝 Next steps:")
        print("   - Admin login: jan@binge.de")
        print("   - Admin password: admin123")
        print("   - You can now use the API reset endpoints with admin authentication")
        
    except Exception as e:
        print(f"❌ Error during operation: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main() 