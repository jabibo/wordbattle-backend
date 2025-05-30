﻿from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.models import User
from app.auth import get_password_hash
from app.dependencies import get_db
from app.utils.email_service import email_service
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

@router.post("/register")
def register(user: RegisterUser, db: Session = Depends(get_db)):
    """Register a new user with username, email, and optional password."""
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

