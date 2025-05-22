from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.models import User, Game, Player
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter(tags=["profile"])

@router.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}

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
