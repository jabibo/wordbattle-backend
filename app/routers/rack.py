from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Player
from app.auth import get_current_user
from app.routers.games import POOL
import random

router = APIRouter(prefix="/rack", tags=["rack"])

@router.get("/")
def get_rack(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get the current user's rack for all active games."""
    players = db.query(Player).filter(Player.user_id == current_user.id).all()
    
    if not players:
        return {"racks": []}
    
    return {
        "racks": [
            {"game_id": player.game_id, "rack": player.rack}
            for player in players
        ]
    }

@router.get("/{game_id}")
def get_game_rack(game_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get the current user's rack for a specific game."""
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    
    return {"rack": player.rack}

@router.post("/{game_id}/refill")
def refill_rack(game_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Refill the rack to 7 letters."""
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    
    needed = 7 - len(player.rack)
    if needed <= 0:
        return {"rack": player.rack, "message": "Rack ist bereits voll"}
    
    new_letters = random.sample(POOL, needed)
    player.rack += "".join(new_letters)
    db.commit()
    
    return {
        "rack": player.rack,
        "new_letters": "".join(new_letters),
        "message": f"{needed} neue Buchstaben hinzugefügt"
    }