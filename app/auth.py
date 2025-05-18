from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app.dependencies import get_db
from app.models import Game

router = APIRouter()

@router.get("/games/{game_id}/check")
def get_game(game_id: str, db: Session = Depends(get_db)):
    result = db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    if not game:
        raise HTTPException(status_code=404, detail="Spiel nicht gefunden")
    return game
