from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Game, Player
from app.auth import get_current_user
import uuid, json, random

POOL = list("ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ"*2 + "EEEEEEEEAAAAAIIIOO") + ["?"]*2

router = APIRouter(prefix="/games", tags=["games"])

@router.post("/")
def create_game(
    game_data: dict = Body(None),
    db: Session = Depends(get_db)
):
    """
    Wenn der Request { "id": "...", "state": "..." } enthält,
    wird diese ID+State übernommen.
    Ansonsten wird automatisch eine neue ID und ein leeres 15×15-Board erzeugt.
    """
    if game_data and game_data.get("id") and game_data.get("state"):
        new_id = game_data["id"]
        state  = game_data["state"]
    else:
        new_id = str(uuid.uuid4())
        state  = json.dumps([[None for _ in range(15)] for _ in range(15)])
    game = Game(id=new_id, state=state)
    db.add(game)
    db.commit()
    return {"id": new_id, "state": state}

@router.get("/{game_id}")
def get_game(game_id: str, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Spiel nicht gefunden")
    return {"id": game.id, "state": game.state, "current_player_id": game.current_player_id}

@router.post("/{game_id}/join")
def join_game(game_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Spiel nicht gefunden")
    if db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first():
        raise HTTPException(status_code=400, detail="Bereits beigetreten")
    rack = "".join(random.sample(POOL, 7))
    player = Player(game_id=game_id, user_id=current_user.id, rack=rack, score=0)
    db.add(player)
    db.commit()
    return {"message": f"Spieler {current_user.username} beigetreten", "rack": rack}

@router.post("/{game_id}/deal")
def deal_letters(game_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    needed = 7 - len(player.rack)
    new_letters = random.sample(POOL, needed)
    player.rack += "".join(new_letters)
    db.commit()
    return {"new_rack": player.rack}

@router.post("/{game_id}/exchange")
def exchange_letters(game_id: str, letters: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    if len(POOL) < len(letters):
        raise HTTPException(status_code=400, detail="Nicht genug Buchstaben im Pool")
    for l in letters:
        if l not in player.rack:
            raise HTTPException(status_code=400, detail=f"Buchstabe {l} nicht im Rack")
        player.rack = player.rack.replace(l, "", 1)
    new_letters = random.sample(POOL, len(letters))
    player.rack += "".join(new_letters)
    db.commit()
    return {"new_rack": player.rack}
