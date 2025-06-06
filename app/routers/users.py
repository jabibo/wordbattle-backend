from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from app.models import User, Game, Player
from app.auth import get_password_hash, get_current_user
from app.db import get_db
from app.dependencies import get_translation_helper
from app.utils.email_service import email_service
from app.utils.i18n import TranslationHelper
from sqlalchemy.future import select
from typing import List, Optional
import logging
import random
import traceback

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
        "allow_invites": current_user.allow_invites,
        "preferred_languages": current_user.preferred_languages or ["en", "de"]
    }

@router.get("/previous-opponents")
def get_previous_opponents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of players the current user has played with before."""
    
    try:
        # Use raw SQL to avoid SQLAlchemy subquery issues (fixed JSON GROUP BY)
        sql_query = text("""
            SELECT 
                u.id, 
                u.username, 
                u.allow_invites, 
                u.preferred_languages,
                opponent_counts.games_together
            FROM (
                SELECT 
                    p2.user_id,
                    COUNT(p2.game_id) as games_together
                FROM players p2
                WHERE p2.game_id IN (
                    SELECT p1.game_id 
                    FROM players p1 
                    WHERE p1.user_id = :current_user_id
                )
                AND p2.user_id != :current_user_id
                GROUP BY p2.user_id
            ) opponent_counts
            JOIN users u ON u.id = opponent_counts.user_id
            WHERE u.allow_invites = true
            ORDER BY opponent_counts.games_together DESC
        """)
        
        result = db.execute(sql_query, {"current_user_id": current_user.id})
        opponents = result.fetchall()
        
        players_info = []
        for opponent in opponents:
            players_info.append({
                "id": opponent.id,
                "username": opponent.username,
                "allow_invites": opponent.allow_invites,
                "preferred_languages": opponent.preferred_languages or ["en", "de"],
                "games_played_together": opponent.games_together
            })
        
        return {
            "previous_opponents": players_info,
            "total_count": len(players_info)
        }
        
    except Exception as e:
        logger.error(f"Error in get_previous_opponents: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return empty list instead of error for better UX
        return {
            "previous_opponents": [],
            "total_count": 0
        }

@router.get("/random-candidates")
def get_random_candidates(
    language: str = Query("en", description="Preferred game language"),
    limit: int = Query(10, description="Maximum number of candidates to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get random users who accept invites and have compatible language preferences."""
    
    try:
        # Simplified approach - just get all users who accept invites
        # Language filtering can be added later when we have more users and proper JSON handling
        candidates = db.query(User).filter(
            User.id != current_user.id,
            User.allow_invites == True
        ).all()
        
        # Randomly shuffle and limit results
        if candidates:
            random.shuffle(candidates)
            candidates = candidates[:limit]
        
        candidates_info = []
        for candidate in candidates:
            candidates_info.append({
                "id": candidate.id,
                "username": candidate.username,
                "preferred_languages": candidate.preferred_languages or ["en", "de"],
                "allow_invites": candidate.allow_invites
            })
        
        return {
            "candidates": candidates_info,
            "total_count": len(candidates_info),
            "language_filter": language
        }
        
    except Exception as e:
        logger.error(f"Error in get_random_candidates: {e}")
        return {
            "candidates": [],
            "total_count": 0,
            "language_filter": language
        }

@router.get("/search")
def search_users(
    username: str = Query(..., description="Username to search for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for users by username (partial match)."""
    
    if len(username.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search term must be at least 2 characters")
    
    try:
        # Search for users with usernames containing the search term
        search_results = db.query(User).filter(
            User.id != current_user.id,  # Exclude current user
            User.username.ilike(f"%{username}%"),  # Partial match, case insensitive
            User.allow_invites == True  # Only show users who accept invites
        ).limit(20).all()  # Limit to 20 results
        
        results_info = []
        for user in search_results:
            results_info.append({
                "id": user.id,
                "username": user.username,
                "preferred_languages": user.preferred_languages or ["en", "de"],
                "allow_invites": user.allow_invites
            })
        
        return {
            "users": results_info,
            "total_count": len(results_info),
            "search_term": username
        }
        
    except Exception as e:
        logger.error(f"Error in search_users: {e}")
        return {
            "users": [],
            "total_count": 0,
            "search_term": username
        }

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

