from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db import get_db
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
import os

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

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = None
    verification_code: str = None

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
    
    return {"success": True, "access_token": access_token, "token_type": "bearer"}

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
    return {"success": True, "message": "OK"}

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
            "email": user.email,
            "language": user.language or "en",
            "is_admin": user.is_admin,
            "is_word_admin": user.is_word_admin
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
    return {"success": True, "message": "OK"}

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
            "email": user.email,
            "language": user.language or "en",
            "is_admin": user.is_admin,
            "is_word_admin": user.is_word_admin
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
    
    return {"success": True, "message": "Successfully logged out"}

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_email_verified": current_user.is_email_verified,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        "language": current_user.language or "en",
        "is_admin": current_user.is_admin,
        "is_word_admin": current_user.is_word_admin
    }

@router.post("/register")
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user or verify email with code."""
    
    # If verification_code is provided, this is an email verification
    if request.verification_code:
        user = get_user_by_email(db, request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification request"
            )
        
        # Check verification code
        now = datetime.now(timezone.utc)
        expires_at = user.verification_code_expires
        
        if expires_at:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            is_expired = expires_at < now
        else:
            is_expired = True
        
        if (not user.verification_code or 
            user.verification_code != request.verification_code or
            is_expired):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )
        
        # Verify email
        user.is_email_verified = True
        user.verification_code = None
        user.verification_code_expires = None
        db.commit()
        
        return {
            "success": True,
            "message": "Email verified successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
    
    # Otherwise, this is a new registration
    else:
        # Check if email already exists
        existing_user = get_user_by_email(db, request.email)
        if existing_user:
            if existing_user.is_email_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                # Resend verification code for unverified user
                verification_code = generate_verification_code()
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
                
                existing_user.verification_code = verification_code
                existing_user.verification_code_expires = expires_at
                if request.username:
                    existing_user.username = request.username
                db.commit()
                
                # Send verification email
                email_service.send_verification_code(
                    to_email=request.email,
                    verification_code=verification_code,
                    username=existing_user.username
                )
                
                return {
                    "success": True,
                    "message": "Verification code sent to email",
                    "requires_verification": True
                }
        
        # Create new user
        from app.models import User
        
        username = request.username or request.email.split('@')[0]
        
        # Check if username is taken
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            # Generate unique username
            import random
            username = f"{username}_{random.randint(1000, 9999)}"
        
        # Generate verification code
        verification_code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
        
        new_user = User(
            username=username,
            email=request.email,
            verification_code=verification_code,
            verification_code_expires=expires_at,
            is_email_verified=False
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Send verification email
        email_service.send_verification_code(
            to_email=request.email,
            verification_code=verification_code,
            username=username
        )
        
        return {
            "success": True,
            "message": "Registration initiated. Please check your email for verification code.",
            "requires_verification": True,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email
            }
        }

# =============================================================================
# CONTRACT-COMPLIANT ENDPOINTS (Aliases/Wrappers)
# =============================================================================

class ContractAuthRequest(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    verification_code: Optional[str] = None

@router.post("/login")
def contract_login(request: ContractAuthRequest, db: Session = Depends(get_db)):
    """Contract-compliant login endpoint (wrapper for email-login flow)."""
    # This endpoint initiates the email login process
    email_login_request = EmailLoginRequest(email=request.email, remember_me=False)
    response = request_email_login(email_login_request, db)
    
    # Return contract-compliant format
    return {
        "success": True,
        "message": response["message"],
        "token_type": "bearer",
        "requires_verification": True
    }

@router.post("/verify")
def contract_verify(request: ContractAuthRequest, db: Session = Depends(get_db)):
    """Contract-compliant verify endpoint (wrapper for verify-code)."""
    if not request.verification_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code is required"
        )
    
    verify_request = VerifyCodeRequest(
        email=request.email,
        verification_code=request.verification_code,
        remember_me=True  # Always enable remember_me for contract compliance
    )
    
    response = verify_login_code(verify_request, db)
    
    # Return contract-compliant format with persistent_token
    return {
        "success": True,
        "access_token": response["access_token"],
        "persistent_token": response.get("persistent_token", ""),  # Include persistent token
        "token_type": response["token_type"],
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "user": {
            "id": str(response["user"]["id"]),
            "username": response["user"]["username"],
            "email": response["user"]["email"],
            "created_at": datetime.now(timezone.utc).isoformat()  # Placeholder
        }
    }

@router.post("/refresh")
def contract_refresh(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Contract-compliant refresh endpoint (creates new access token)."""
    # Create new access token for current user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.email}, 
        expires_delta=access_token_expires
    )
    
    # Create/refresh persistent token
    persistent_token = create_persistent_token(data={"sub": current_user.email})
    persistent_token_expires = datetime.now(timezone.utc) + timedelta(days=30)
    
    # Store persistent token in database
    current_user.persistent_token = persistent_token
    current_user.persistent_token_expires = persistent_token_expires
    current_user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Return contract-compliant format with persistent_token
    return {
        "success": True,
        "access_token": access_token,
        "persistent_token": persistent_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "user": {
            "id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else datetime.now(timezone.utc).isoformat()
        }
    }

@router.post("/simple-admin-login")
async def simple_admin_login(
    email: str,
    db: Session = Depends(get_db)
):
    """
    DEBUG ENDPOINT: Simple admin login without email verification for testing.
    This bypasses the email verification flow for easier testing.
    
    ⚠️ WARNING: This is for development/testing only!
    """
    # Disable in production
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=403, detail="Debug endpoints disabled in production")
    
    try:
        # Find user by email
        user = get_user_by_email(db, email)
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User with email {email} not found")
        
        # Create access token directly (bypass email verification)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, 
            expires_delta=access_token_expires
        )
        
        # Create persistent token for debug login
        persistent_token = create_persistent_token(data={"sub": user.email})
        persistent_token_expires = datetime.now(timezone.utc) + timedelta(days=30)
        
        # Update user and store persistent token
        user.persistent_token = persistent_token
        user.persistent_token_expires = persistent_token_expires
        user.last_login = datetime.now(timezone.utc)
        user.is_email_verified = True  # Mark as verified for testing
        db.commit()
        
        return {
            "success": True,
            "message": f"Debug login successful for {user.username}",
            "access_token": access_token,
            "persistent_token": persistent_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),  # Convert to string for contract compliance
                "username": user.username,
                "email": user.email,
                "language": user.language or "en",
                "is_admin": user.is_admin,
                "is_word_admin": user.is_word_admin
            },
            "warning": "This is a debug endpoint - not for production use"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug login error: {str(e)}")
