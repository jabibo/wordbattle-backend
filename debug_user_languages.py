import asyncio
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:your_password@localhost:5432/wordbattle_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_user_languages():
    """Debug user language preferences"""
    db = SessionLocal()
    try:
        print("🔍 Debugging User Language Preferences")
        print("=" * 60)
        
        users = db.query(User).all()
        print(f"Found {len(users)} users:")
        print()
        
        for user in users:
            print(f"👤 User: {user.username}")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Language (UI): {user.language}")
            print(f"   Preferred Languages (invites): {user.preferred_languages}")
            print(f"   Allow Invites: {user.allow_invites}")
            print(f"   Created: {user.created_at}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_user_languages() 