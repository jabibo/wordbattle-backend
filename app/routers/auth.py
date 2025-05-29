from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import User
from app.auth import (
    verify_password, create_access_token, get_user_by_username, 
    get_user_by_email, generate_verification_code, generate_persistent_token,
    create_persistent_token, get_current_user
)
from datetime import timedelta, datetime, timezone
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, VERIFICATION_CODE_EXPIRE_MINUTES
from app.utils.email_service import email_service
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

class EmailLoginRequest(BaseModel):
    email: EmailStr
    remember_me: bool = False

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    verification_code: str
    remember_me: bool = False

class PersistentLoginRequest(BaseModel):
    persistent_token: str

@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Legacy login endpoint for backward compatibility with username/password."""
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/email-login")
def request_email_login(request: EmailLoginRequest, db: Session = Depends(get_db)):
    """Request login with email - sends verification code."""
    user = get_user_by_email(db, request.email)
    if not user:
        # For security, don't reveal if email exists or not
        return {
            "message": "If this email is registered, you will receive a verification code.",
            "email_sent": True
        }
    
    # Generate verification code
    verification_code = generate_verification_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
    
    # Store verification code in database
    user.verification_code = verification_code
    user.verification_code_expires = expires_at
    db.commit()
    
    # Send verification code via email
    email_sent = email_service.send_verification_code(
        to_email=request.email,
        verification_code=verification_code,
        username=user.username
    )
    
    if not email_sent:
        logger.error(f"Failed to send verification code to {request.email}")
        # Don't reveal the failure to the user for security
    
    return {
        "message": "If this email is registered, you will receive a verification code.",
        "email_sent": True,
        "expires_in_minutes": VERIFICATION_CODE_EXPIRE_MINUTES
    }

@router.options("/email-login")
def email_login_options():
    """Handle OPTIONS preflight for email-login endpoint."""
    return {"message": "OK"}

@router.post("/verify-code")
def verify_login_code(request: VerifyCodeRequest, db: Session = Depends(get_db)):
    """Verify the email login code and return access token."""
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code",
        )
    
    # Check if verification code is valid and not expired
    now = datetime.now(timezone.utc)
    expires_at = user.verification_code_expires
    
    # Simple timezone-safe comparison
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        is_expired = expires_at < now
    else:
        is_expired = True
    
    if (not user.verification_code or 
        user.verification_code != request.verification_code or
        not user.verification_code_expires or
        is_expired):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification code",
        )
    
    # Clear verification code after successful verification
    user.verification_code = None
    user.verification_code_expires = None
    user.is_email_verified = True
    user.last_login = datetime.now(timezone.utc)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }
    
    # If remember_me is requested, create persistent token
    if request.remember_me:
        persistent_token = create_persistent_token(data={"sub": user.email})
        persistent_token_expires = datetime.now(timezone.utc) + timedelta(days=30)
        
        # Store persistent token in database
        user.persistent_token = persistent_token
        user.persistent_token_expires = persistent_token_expires
        
        response_data["persistent_token"] = persistent_token
        response_data["persistent_expires_at"] = persistent_token_expires.isoformat()
    
    db.commit()
    
    return response_data

@router.options("/verify-code")
def verify_code_options():
    """Handle OPTIONS preflight for verify-code endpoint."""
    return {"message": "OK"}

@router.post("/persistent-login")
def login_with_persistent_token(request: PersistentLoginRequest, db: Session = Depends(get_db)):
    """Login using a persistent token (for 'remember me' functionality)."""
    # Find user by persistent token
    user = db.query(User).filter(
        User.persistent_token == request.persistent_token,
        User.persistent_token_expires > datetime.now(timezone.utc)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired persistent token",
        )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

@router.post("/logout")
def logout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Logout user and invalidate persistent token."""
    if current_user:
        # Clear persistent token
        current_user.persistent_token = None
        current_user.persistent_token_expires = None
        db.commit()
    
    return {"message": "Successfully logged out"}

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_email_verified": current_user.is_email_verified,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }
