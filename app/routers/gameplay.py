
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Game, Player, User
import random
import string

router = APIRouter(prefix="/games", tags=["gameplay"])

POOL = list("ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ"*2 + "EEEEEEEEAAAAAIIIOO") + ["?"]*2

def draw_letters(pool, count):
    return random.sample(pool, count)

@router.post("/{game_id}/join/{user_id}")
def join_game(game_id: str, user_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Spiel nicht gefunden")
    if db.query(Player).filter_by(game_id=game_id, user_id=user_id).first():
        raise HTTPException(status_code=400, detail="Spieler bereits beigetreten")
    rack = "".join(draw_letters(POOL, 7))
    player = Player(game_id=game_id, user_id=user_id, rack=rack, score=0)
    db.add(player)
    db.commit()
    return {"message": f"Spieler {user_id} Spiel {game_id} beigetreten", "rack": rack}

@router.post("/{game_id}/deal/{user_id}")
def deal_letters(game_id: str, user_id: int, db: Session = Depends(get_db)):
    player = db.query(Player).filter_by(game_id=game_id, user_id=user_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    needed = 7 - len(player.rack)
    new_letters = draw_letters(POOL, needed)
    player.rack += "".join(new_letters)
    db.commit()
    return {"new_rack": player.rack}

@router.post("/{game_id}/exchange/{user_id}")
def exchange_letters(game_id: str, user_id: int, letters: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter_by(game_id=game_id, user_id=user_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    if len(POOL) < len(letters):
        raise HTTPException(status_code=400, detail="Nicht genug Buchstaben im Pool")
    for l in letters:
        if l not in player.rack:
            raise HTTPException(status_code=400, detail=f"Buchstabe {l} nicht im Rack")
        player.rack = player.rack.replace(l, "", 1)
    new_letters = draw_letters(POOL, len(letters))
    player.rack += "".join(new_letters)
    db.commit()
    return {"new_rack": player.rack}
