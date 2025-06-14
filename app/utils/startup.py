"""
Startup utilities for WordBattle backend.
Handles initialization tasks like ensuring admin user exists.
"""

import os
import secrets
import string
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.auth import get_password_hash
import logging

logger = logging.getLogger(__name__)

def generate_secure_password(length: int = 12) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def ensure_admin_user_exists() -> dict:
    """
    Ensure that the admin user defined in environment variables exists.
    Creates the admin user if they don't exist.
    
    Returns:
        dict: Status information about the admin user operation
    """
    admin_username = os.environ.get("ADMIN_USERNAME")
    admin_email = os.environ.get("ADMIN_EMAIL")
    
    if not admin_username or not admin_email:
        logger.info("No ADMIN_USERNAME or ADMIN_EMAIL configured - skipping admin user creation")
        return {
            "status": "skipped",
            "reason": "No admin credentials configured in environment",
            "admin_username": None,
            "admin_email": None
        }
    
    try:
        db = next(get_db())
        
        # Check if admin user already exists (by username or email)
        existing_admin = db.query(User).filter(
            (User.username == admin_username) | (User.email == admin_email)
        ).first()
        
        if existing_admin:
            # Update admin status if user exists but isn't admin
            if not existing_admin.is_admin:
                existing_admin.is_admin = True
                db.commit()
                logger.info(f"Promoted existing user '{existing_admin.username}' to admin")
                return {
                    "status": "promoted",
                    "admin_username": existing_admin.username,
                    "admin_email": existing_admin.email,
                    "admin_id": existing_admin.id,
                    "message": f"Promoted existing user to admin"
                }
            else:
                logger.info(f"Admin user '{existing_admin.username}' already exists")
                return {
                    "status": "exists",
                    "admin_username": existing_admin.username,
                    "admin_email": existing_admin.email,
                    "admin_id": existing_admin.id,
                    "message": f"Admin user already exists"
                }
        
        # Generate secure password for new admin
        admin_password = generate_secure_password(16)
        
        # Create new admin user
        admin_user = User(
            username=admin_username,
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            is_admin=True,
            is_email_verified=True,  # Admin is pre-verified
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"Created admin user '{admin_username}' with email '{admin_email}'")
        logger.warning(f"🔑 ADMIN PASSWORD: {admin_password}")
        logger.warning("⚠️  Please save this password securely and change it after first login!")
        
        return {
            "status": "created",
            "admin_username": admin_user.username,
            "admin_email": admin_user.email,
            "admin_id": admin_user.id,
            "admin_password": admin_password,
            "message": f"Created admin user '{admin_username}'",
            "warning": "Save the password securely and change it after first login!"
        }
        
    except Exception as e:
        logger.error(f"Failed to ensure admin user exists: {str(e)}")
        return {
            "status": "error",
            "admin_username": admin_username,
            "admin_email": admin_email,
            "error": str(e),
            "message": "Failed to create/verify admin user"
        }
    finally:
        if 'db' in locals():
            db.close()

def startup_tasks() -> dict:
    """
    Run all startup tasks.
    
    Returns:
        dict: Summary of all startup task results
    """
    logger.info("🚀 Running startup tasks...")
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "tasks": {}
    }
    
    # Task 1: Ensure admin user exists
    logger.info("📋 Task 1: Ensuring admin user exists...")
    admin_result = ensure_admin_user_exists()
    results["tasks"]["admin_user"] = admin_result
    
    # Add more startup tasks here as needed
    # Task 2: Database migrations check
    # Task 3: Contract validation setup
    # etc.
    
    logger.info("✅ Startup tasks completed")
    return results

if __name__ == "__main__":
    # Allow running this module directly for testing
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    result = startup_tasks()
    print(f"Startup tasks result: {result}") 