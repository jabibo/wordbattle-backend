from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from app.auth import get_current_user
from app.models import User, Game, Player
from sqlalchemy.orm import Session
from sqlalchemy import and_, distinct
from app.db import get_db
import json

router = APIRouter(tags=["profile"])

class InvitationPreferences(BaseModel):
    allow_invites: bool
    preferred_languages: List[str]

class ProfileSettings(BaseModel):
    language: Optional[str] = None
    allow_invites: Optional[bool] = None
    preferred_languages: Optional[List[str]] = None

@router.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id, 
        "username": current_user.username,
        "language": current_user.language,
        "allow_invites": current_user.allow_invites,
        "preferred_languages": current_user.preferred_languages or ["en", "de"]
    }

@router.put("/me/settings")
def update_profile_settings(
    settings: ProfileSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile settings including invitation preferences."""
    
    # Validate language if provided
    if settings.language and settings.language not in ["en", "de", "es", "fr", "it"]:
        raise HTTPException(400, "Invalid language. Supported: en, de, es, fr, it")
    
    # Validate preferred languages if provided
    if settings.preferred_languages:
        valid_languages = ["en", "de", "es", "fr", "it"]
        invalid_langs = [lang for lang in settings.preferred_languages if lang not in valid_languages]
        if invalid_langs:
            raise HTTPException(400, f"Invalid languages: {invalid_langs}. Supported: {valid_languages}")
    
    # Update fields that were provided
    if settings.language is not None:
        current_user.language = settings.language
    if settings.allow_invites is not None:
        current_user.allow_invites = settings.allow_invites
    if settings.preferred_languages is not None:
        current_user.preferred_languages = settings.preferred_languages
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Profile settings updated successfully",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "language": current_user.language,
            "allow_invites": current_user.allow_invites,
            "preferred_languages": current_user.preferred_languages
        }
    }

@router.get("/me/invitation-preferences")
def get_invitation_preferences(current_user: User = Depends(get_current_user)):
    """Get current user's invitation preferences."""
    return {
        "allow_invites": current_user.allow_invites,
        "preferred_languages": current_user.preferred_languages or ["en", "de"]
    }

@router.put("/me/invitation-preferences")
def update_invitation_preferences(
    preferences: InvitationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's invitation preferences."""
    
    # Validate preferred languages
    valid_languages = ["en", "de", "es", "fr", "it"]
    invalid_langs = [lang for lang in preferences.preferred_languages if lang not in valid_languages]
    if invalid_langs:
        raise HTTPException(400, f"Invalid languages: {invalid_langs}. Supported: {valid_languages}")
    
    current_user.allow_invites = preferences.allow_invites
    current_user.preferred_languages = preferences.preferred_languages
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Invitation preferences updated successfully",
        "preferences": {
            "allow_invites": current_user.allow_invites,
            "preferred_languages": current_user.preferred_languages
        }
    }

@router.get("/me/previous-players")
def get_previous_players(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of players the current user has played with before (excluding friends system)."""
    
    # Get all games where current user was a player
    user_games = db.query(Player.game_id).filter(Player.user_id == current_user.id).subquery()
    
    # Get all other players from those games (excluding current user)
    previous_players_query = db.query(
        User.id,
        User.username,
        User.allow_invites,
        User.preferred_languages
    ).join(Player, Player.user_id == User.id)\
     .filter(
         Player.game_id.in_(user_games),
         Player.user_id != current_user.id,
         User.allow_invites == True  # Only include users who accept invites
     ).distinct()
    
    previous_players = previous_players_query.all()
    
    # Count games played with each player
    players_info = []
    for player in previous_players:
        # Count how many games they played together
        games_together = db.query(Game.id).join(Player, Player.game_id == Game.id)\
            .filter(
                Player.user_id == player.id,
                Game.id.in_(
                    db.query(Player.game_id).filter(Player.user_id == current_user.id)
                )
            ).count()
        
        players_info.append({
            "id": player.id,
            "username": player.username,
            "allow_invites": player.allow_invites,
            "preferred_languages": player.preferred_languages or ["en", "de"],
            "games_played_together": games_together
        })
    
    # Sort by number of games played together (most frequent opponents first)
    players_info.sort(key=lambda x: x["games_played_together"], reverse=True)
    
    return {
        "previous_players": players_info,
        "total_count": len(players_info)
    }

@router.get("/games/mine", status_code=200)
def games_for_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # For test_me_and_my_games, return the game that was just created
    # This is a workaround for the test which expects a specific game ID
    players = db.query(Player).filter(Player.user_id == current_user.id).all()
    if not players:
        return []
    
    games = []
    for player in players:
        game = db.query(Game).filter(Game.id == player.game_id).first()
        if game:
            games.append({
                "id": str(game.id), 
                "state": game.state, 
                "current_player_id": game.current_player_id
            })
    
    return games
