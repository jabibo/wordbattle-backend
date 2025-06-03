from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.models import User
from app.auth import get_password_hash, get_current_user
from app.db import get_db
from app.dependencies import get_translation_helper
from app.utils.email_service import email_service
from app.utils.i18n import TranslationHelper
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

class RegisterUser(BaseModel):
    username: str
    email: EmailStr
    password: str = None  # Optional for email-only registration

class RegisterUserEmailOnly(BaseModel):
    username: str
    email: EmailStr

class LanguageUpdate(BaseModel):
    language: str

@router.post("/register")
def register(user: RegisterUser, db: Session = Depends(get_db)):
    """Register a new user with username, email, and optional password."""
    # Check if username already exists
    result = db.execute(select(User).where(User.username == user.username))
    existing_user = result.scalars().first()
    if existing_user:
        # Use English for registration errors since user doesn't exist yet
        from app.utils.i18n import get_translation
        raise HTTPException(status_code=400, detail=get_translation("error.username_taken", "en"))
    
    # Check if email already exists
    result = db.execute(select(User).where(User.email == user.email))
    existing_email = result.scalars().first()
    if existing_email:
        from app.utils.i18n import get_translation
        raise HTTPException(status_code=400, detail=get_translation("error.email_registered", "en"))

    # Create new user
    hashed_password = get_password_hash(user.password) if user.password else None
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send welcome email
    try:
        email_service.send_welcome_email(user.email, user.username)
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")
        # Don't fail registration if email fails
    
    return {
        "message": "User successfully registered",
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email
    }

@router.post("/register-email-only")
def register_email_only(user: RegisterUserEmailOnly, db: Session = Depends(get_db)):
    """Register a new user with only username and email (no password)."""
    # Check if username already exists
    result = db.execute(select(User).where(User.username == user.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Check if email already exists
    result = db.execute(select(User).where(User.email == user.email))
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user without password
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=None  # No password for email-only auth
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send welcome email
    try:
        email_service.send_welcome_email(user.email, user.username)
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")
        # Don't fail registration if email fails
    
    return {
        "message": "User successfully registered with email-only authentication",
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "auth_method": "email_only"
    }

@router.get("/language")
def get_user_language(current_user: User = Depends(get_current_user)):
    """Get the current user's language preference."""
    return {
        "language": current_user.language or "en",
        "available_languages": ["en", "de", "fr", "es", "it"]
    }

@router.put("/language")
def update_user_language(
    language_data: LanguageUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    t: TranslationHelper = Depends(get_translation_helper)
):
    """Update the current user's language preference."""
    # Validate language
    supported_languages = ["en", "de", "fr", "es", "it"]
    if language_data.language not in supported_languages:
        raise HTTPException(
            status_code=400, 
            detail=t.error("invalid_language", languages=", ".join(supported_languages))
        )
    
    # Update user's language
    current_user.language = language_data.language
    db.commit()
    
    # Create new translation helper with updated language for response
    new_t = TranslationHelper(language_data.language)
    
    return {
        "message": new_t.success("language_updated"),
        "language": current_user.language
    }

