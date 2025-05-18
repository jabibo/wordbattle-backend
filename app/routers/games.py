from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Game
import uuid
import json

router = APIRouter(prefix="/games", tags=["games"])

@router.post("/")
def create_game(db: Session = Depends(get_db)):
    new_id = str(uuid.uuid4())
    empty_board = json.dumps([[None for _ in range(15)] for _ in range(15)])
    game = Game(id=new_id, state=empty_board)
    db.add(game)
    db.commit()
    return {"id": new_id, "state": empty_board}

@router.get("/{game_id}")
def get_game(game_id: str, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    return game or {"error": "not found"}
