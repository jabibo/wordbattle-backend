from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.dependencies import get_translation_helper
from app.models import Player, Game
from app.auth import get_current_user
from app.utils.i18n import TranslationHelper
from app.game_logic.letter_bag import LETTER_DISTRIBUTION
import random

router = APIRouter(prefix="/rack", tags=["rack"])

@router.get("/")
def get_rack(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    """Get the current user's rack for all active games."""
    players = db.query(Player).filter(Player.user_id == current_user.id).all()
    
    if not players:
        return {"racks": []}
    
    return {
        "racks": [
            {"game_id": player.game_id, "rack": list(player.rack)}
            for player in players
        ]
    }

@router.get("/{game_id}")
def get_game_rack(
    game_id: str, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user),
    t: TranslationHelper = Depends(get_translation_helper)
):
    """Get the current user's rack for a specific game."""
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    
    if not player:
        raise HTTPException(status_code=404, detail=t.error("player_not_found"))
    
    return {"rack": list(player.rack)}

@router.post("/{game_id}/refill")
def refill_rack(
    game_id: str, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user),
    t: TranslationHelper = Depends(get_translation_helper)
):
    """Refill the rack to 7 letters."""
    # Get both player and game info to know the language
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    if not player:
        raise HTTPException(status_code=404, detail=t.error("player_not_found"))
    
    game = db.query(Game).filter_by(id=game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail=t.error("game_not_found"))
    
    needed = 7 - len(player.rack)
    if needed <= 0:
        return {"new_rack": list(player.rack)}
    
    # Create pool of available letters based on language-specific distribution
    pool = []
    distribution = LETTER_DISTRIBUTION[game.language]["frequency"]
    for letter, count in distribution.items():
        pool.extend([letter] * count)
    
    new_letters = random.sample(pool, needed)
    new_rack = player.rack + "".join(new_letters)
    player.rack = new_rack
    db.commit()
    
    return {"new_rack": list(new_rack)}