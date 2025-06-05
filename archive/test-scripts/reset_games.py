#!/usr/bin/env python3
"""
Reset Games Database Script

This script clears all game-related data from the database while preserving:
- Users
- WordLists

It will delete:
- Games
- Players
- Moves
- Game Invitations
- Chat Messages
"""

import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Game, Player, Move, GameInvitation, ChatMessage

def reset_games_data():
    """Reset all game-related data in the database."""
    db = SessionLocal()
    
    try:
        print("🗑️  Starting database reset...")
        
        # Delete in order to respect foreign key constraints
        tables_to_clear = [
            ("Chat Messages", ChatMessage),
            ("Moves", Move),
            ("Players", Player),
            ("Game Invitations", GameInvitation),
            ("Games", Game),
        ]
        
        for table_name, model in tables_to_clear:
            count = db.query(model).count()
            if count > 0:
                print(f"🔄 Deleting {count} {table_name}...")
                db.query(model).delete()
            else:
                print(f"✅ {table_name}: Already empty")
        
        # Reset auto-increment sequences (PostgreSQL)
        print("🔄 Resetting sequences...")
        try:
            # Reset sequences for tables that might have auto-increment IDs
            sequences_to_reset = [
                "moves_id_seq",
                "players_id_seq", 
                "game_invitations_id_seq",
                "chat_messages_id_seq"
            ]
            
            for seq in sequences_to_reset:
                try:
                    db.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1"))
                    print(f"✅ Reset sequence: {seq}")
                except Exception as e:
                    print(f"⚠️  Sequence {seq} not found or already reset: {e}")
                    
        except Exception as e:
            print(f"⚠️  Could not reset sequences (might be SQLite): {e}")
        
        # Commit all changes
        db.commit()
        print("✅ Database reset completed successfully!")
        
        # Show remaining data counts
        print("\n📊 Remaining data:")
        from app.models import User, WordList
        
        user_count = db.query(User).count()
        wordlist_count = db.query(WordList).count()
        
        print(f"   Users: {user_count}")
        print(f"   WordLists: {wordlist_count}")
        print(f"   Games: {db.query(Game).count()}")
        print(f"   Players: {db.query(Player).count()}")
        print(f"   Moves: {db.query(Move).count()}")
        print(f"   Game Invitations: {db.query(GameInvitation).count()}")
        print(f"   Chat Messages: {db.query(ChatMessage).count()}")
        
    except Exception as e:
        print(f"❌ Error during reset: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def confirm_reset():
    """Ask for user confirmation before proceeding."""
    print("⚠️  WARNING: This will delete ALL game-related data!")
    print("   - All games and their state")
    print("   - All player records")
    print("   - All moves history")
    print("   - All game invitations")
    print("   - All chat messages")
    print()
    print("✅ This will PRESERVE:")
    print("   - User accounts")
    print("   - WordLists")
    print()
    
    response = input("Are you sure you want to proceed? (type 'yes' to confirm): ")
    return response.lower() == 'yes'

if __name__ == "__main__":
    print("🎮 WordBattle Database Reset Tool")
    print("=" * 40)
    
    if confirm_reset():
        reset_games_data()
        print("\n🎉 Reset complete! You can now start fresh games.")
    else:
        print("❌ Reset cancelled.") 