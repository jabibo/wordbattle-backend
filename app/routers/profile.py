from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.models import User, Game, Player
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter(tags=["profile"])

@router.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}

@router.get("/games/mine")
def games_for_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    games = db.query(Game).join(Player).filter(Player.user_id == current_user.id).all()
    return [
        {"id": str(g.id), "state": g.state, "current_player_id": g.current_player_id}
        for g in games
    ]
    return [
        {"id": str(g.id), "state": g.state, "current_player_id": g.current_player_id}
        for g in games
    ]
