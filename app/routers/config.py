from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["config"])

class ConfigResponse(BaseModel):
    success: bool
    config: Dict[str, Any]

@router.get("/config")
def get_api_config():
    """Get API configuration for frontend (Contract-compliant endpoint)."""
    
    config = {
        "api_version": "1.0.0",
        "environment": "testing",  # This would be dynamic in production
        "features": {
            "email_verification": True,
            "persistent_login": True,
            "game_invitations": True,
            "computer_players": True,
            "word_challenges": True
        },
        "game": {
            "supported_languages": ["en", "de", "es", "fr", "it"],
            "max_players": 4,
            "min_players": 2,
            "default_time_limit": 0,  # No time limit by default
            "difficulties": ["easy", "normal", "hard"],
            "computer_difficulties": ["easy", "medium", "hard"]
        },
        "auth": {
            "verification_code_length": 6,
            "verification_code_expires_minutes": 15,
            "access_token_expires_minutes": 60,
            "persistent_token_expires_days": 30
        },
        "limits": {
            "max_games_per_user": 100,
            "max_invitations_per_game": 10,
            "rate_limit_requests_per_minute": 60
        },
        "ui": {
            "default_language": "en",
            "available_themes": ["light", "dark"],
            "default_theme": "light"
        }
    }
    
    return {
        "success": True,
        "config": config
    } 