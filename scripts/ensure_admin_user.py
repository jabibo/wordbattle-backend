#!/usr/bin/env python3
"""
Ensure admin user script
Ensures that jan@binge.de exists as an admin user in the database.
This should be run for both production and testing environments.
"""

import os
import sys
import asyncio
from datetime import datetime, timezone

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User
from app.database import get_db
from sqlalchemy.orm import Session

def ensure_admin_user():
    """Ensure that jan@binge.de exists and has admin privileges."""
    
    admin_email = "jan@binge.de"
    admin_username = "janbinge"
    
    print(f"🔍 Checking admin user: {admin_email}")
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == admin_email).first()
        
        if existing_user:
            # User exists - check if admin
            if existing_user.is_admin:
                print(f"✅ Admin user {admin_email} already exists with admin privileges")
                print(f"   Username: {existing_user.username}")
                print(f"   ID: {existing_user.id}")
                print(f"   Created: {existing_user.created_at}")
                print(f"   Is Admin: {existing_user.is_admin}")
                print(f"   Is Word Admin: {existing_user.is_word_admin}")
                return True
            else:
                # User exists but is not admin - upgrade to admin
                print(f"⚠️  User {admin_email} exists but is not admin. Upgrading...")
                existing_user.is_admin = True
                existing_user.is_word_admin = True  # Also grant word admin privileges
                db.commit()
                print(f"✅ User {admin_email} upgraded to admin successfully")
                return True
        else:
            # User doesn't exist - create new admin user
            print(f"⚠️  Admin user {admin_email} does not exist. Creating...")
            
            # Check if username is taken
            username_taken = db.query(User).filter(User.username == admin_username).first()
            if username_taken:
                admin_username = f"{admin_username}_admin"
                print(f"   Username '{admin_username}' taken, using '{admin_username}'")
            
            new_admin = User(
                username=admin_username,
                email=admin_email,
                is_admin=True,
                is_word_admin=True,
                is_email_verified=True,  # Pre-verify admin email
                language="en",
                allow_invites=True,
                preferred_languages=["en", "de"],
                created_at=datetime.now(timezone.utc)
            )
            
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            
            print(f"✅ Admin user created successfully!")
            print(f"   Email: {new_admin.email}")
            print(f"   Username: {new_admin.username}")
            print(f"   ID: {new_admin.id}")
            print(f"   Is Admin: {new_admin.is_admin}")
            print(f"   Is Word Admin: {new_admin.is_word_admin}")
            return True
            
    except Exception as e:
        print(f"❌ Error ensuring admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def check_admin_status():
    """Check current admin users in database."""
    print("📋 Current admin users:")
    
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        admin_users = db.query(User).filter(User.is_admin == True).all()
        
        if not admin_users:
            print("   ⚠️  No admin users found!")
            return False
        
        for user in admin_users:
            print(f"   👤 {user.email} ({user.username}) - ID: {user.id}")
            print(f"      Admin: {user.is_admin}, Word Admin: {user.is_word_admin}")
            print(f"      Created: {user.created_at}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking admin status: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Admin User Management Script")
    print("=" * 40)
    
    # Check current environment
    environment = os.getenv("ENVIRONMENT", "unknown")
    database_url = os.getenv("DATABASE_URL", "not_set")
    
    print(f"Environment: {environment}")
    print(f"Database: {database_url[:50]}..." if len(database_url) > 50 else database_url)
    print()
    
    # Check current admin status
    print("Step 1: Checking current admin users...")
    check_admin_status()
    
    # Ensure admin user exists
    print("Step 2: Ensuring jan@binge.de has admin privileges...")
    success = ensure_admin_user()
    
    if success:
        print("\nStep 3: Final verification...")
        check_admin_status()
        print("🎉 Admin user management completed successfully!")
    else:
        print("❌ Admin user management failed!")
        sys.exit(1) 