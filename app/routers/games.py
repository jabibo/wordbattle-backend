# app/routers/games.py

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Game, Player
from app.auth import get_current_user
from app.game_logic.rules import get_next_player
import uuid, json, random

POOL = list("ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ"*2 + "EEEEEEEEAAAAAIIIOO") + ["?"]*2

router = APIRouter(prefix="/games", tags=["games"])

@router.post("/")
def create_game(
    game_data: dict = Body(None),
    db: Session = Depends(get_db)
):
    if game_data and game_data.get("id") and game_data.get("state"):
        new_id, state = game_data["id"], game_data["state"]
    else:
        new_id = str(uuid.uuid4())
        state  = json.dumps([[None]*15 for _ in range(15)])
    game = Game(id=new_id, state=state)
    db.add(game); db.commit()
    return {"id": new_id, "state": state}


@router.post("/{game_id}/join")
def join_game(game_id: str,
              db: Session = Depends(get_db),
              current_user=Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Spiel nicht gefunden")
    if db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first():
        raise HTTPException(400, "Bereits beigetreten")
    rack = "".join(random.sample(POOL, 7))
    player = Player(game_id=game_id, user_id=current_user.id, rack=rack, score=0)
    db.add(player); db.commit()
    return {"rack": rack}


@router.post("/{game_id}/start")
def start_game(game_id: str,
               db: Session = Depends(get_db),
               current_user=Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Spiel nicht gefunden")
    players = db.query(Player).filter(Player.game_id == game_id).all()
    if len(players) < 2:
        raise HTTPException(400, "Nicht genug Spieler zum Starten")
    if current_user.id not in [p.user_id for p in players]:
        raise HTTPException(403, "Du bist kein Teilnehmer")
    if game.current_player_id:
        raise HTTPException(400, "Spiel bereits gestartet")
    first = players[0].user_id
    game.current_player_id = first
    db.commit()
    return {"current_player_id": first}


@router.post("/{game_id}/deal")
def deal_letters(game_id: str,
                 db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game.current_player_id != current_user.id:
        raise HTTPException(403, "Nicht Dein Zug")
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    needed = 7 - len(player.rack)
    new = random.sample(POOL, needed)
    player.rack += "".join(new)
    db.commit()
    # Rotation
    ids = [p.user_id for p in db.query(Player).filter(Player.game_id == game_id).order_by(Player.id)]
    nxt = get_next_player(ids, current_user.id)
    game.current_player_id = nxt; db.commit()
    return {"new_rack": player.rack, "next_player_id": nxt}


@router.post("/{game_id}/exchange")
def exchange_letters(game_id: str,
                     letters: str,
                     db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game.current_player_id != current_user.id:
        raise HTTPException(403, "Nicht Dein Zug")
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    for l in letters:
        if l not in player.rack:
            raise HTTPException(400, f"Buchstabe {l} nicht im Rack")
        player.rack = player.rack.replace(l, "", 1)
    new = random.sample(POOL, len(letters))
    player.rack += "".join(new)
    db.commit()
    # Rotation
    ids = [p.user_id for p in db.query(Player).filter(Player.game_id == game_id).order_by(Player.id)]
    nxt = get_next_player(ids, current_user.id)
    game.current_player_id = nxt; db.commit()
    return {"new_rack": player.rack, "next_player_id": nxt}


@router.post("/{game_id}/pass")
def pass_turn(game_id: str,
              db: Session = Depends(get_db),
              current_user=Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game.current_player_id != current_user.id:
        raise HTTPException(403, "Nicht Dein Zug")
    ids = [p.user_id for p in db.query(Player).filter(Player.game_id == game_id).order_by(Player.id)]
    nxt = get_next_player(ids, current_user.id)
    game.current_player_id = nxt; db.commit()
    return {"message": "Zug gepasst", "next_player_id": nxt}
