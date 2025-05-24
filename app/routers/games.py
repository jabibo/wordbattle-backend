# app/routers/games.py

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Game, Player
from app.auth import get_current_user
from app.game_logic.rules import get_next_player
from app.game_logic.game_completion import check_game_completion, finalize_game
from app.config import LETTER_POOL_SIZE
from app.utils.wordlist_utils import ensure_wordlist_available
import uuid, json, random

from app.game_logic.letter_bag import create_rack, LETTER_DISTRIBUTION

# For backward compatibility
POOL = []
for letter, count in LETTER_DISTRIBUTION.items():
    POOL.extend([letter] * count)

router = APIRouter(prefix="/games", tags=["games"])

@router.get("/{game_id}")
def get_game(game_id: str, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Spiel nicht gefunden")
    return {"id": game.id, "state": game.state, "current_player_id": game.current_player_id}

@router.post("/")
def create_game(
    game_data: dict = Body(None),
    db: Session = Depends(get_db)
):
    if game_data and game_data.get("id") and game_data.get("state"):
        new_id, state = game_data["id"], game_data["state"]
    else:
        new_id = str(uuid.uuid4())
        state = json.dumps({
            "board": [[None]*15 for _ in range(15)],
            "language": "de"  # Default language
        })
    
    # Ensure default German wordlist is available
    ensure_wordlist_available("de", db)
    
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
    rack = create_rack()
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
    if not game:
        raise HTTPException(404, "Spiel nicht gefunden")
    
    # For testing purposes, allow dealing if current_player_id is None
    if game.current_player_id is not None and game.current_player_id != current_user.id:
        raise HTTPException(403, "Nicht Dein Zug")
    
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    if not player:
        raise HTTPException(404, "Spieler nicht gefunden")
    needed = LETTER_POOL_SIZE - len(player.rack)
    if needed > 0:
        new_letters = random.sample(POOL, needed)
        player.rack += "".join(new_letters)
        db.commit()
    else:
        new_letters = []
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
    
    # Verify all letters are in the rack
    rack_copy = player.rack
    for l in letters:
        if l not in rack_copy:
            raise HTTPException(400, f"Buchstabe {l} nicht im Rack")
        rack_copy = rack_copy.replace(l, "", 1)
    
    # Remove the letters to exchange from the rack
    for l in letters:
        player.rack = player.rack.replace(l, "", 1)
    
    # Draw new letters
    new_letters = random.sample(POOL, len(letters))
    player.rack += "".join(new_letters)
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
    
    # Record the pass as an empty move
    from app.models import Move
    from datetime import datetime, timezone
    move_entry = Move(
        game_id=game_id,
        player_id=current_user.id,
        move_data=json.dumps([]),  # Empty move data indicates a pass
        timestamp=datetime.now(timezone.utc)
    )
    db.add(move_entry)
    
    # Check if the game is complete after this pass
    is_complete, completion_data = check_game_completion(game_id, db)
    
    # Rotation
    ids = [p.user_id for p in db.query(Player).filter(Player.game_id == game_id).order_by(Player.id)]
    nxt = get_next_player(ids, current_user.id)
    game.current_player_id = nxt
    db.commit()
    
    result = {"message": "Zug gepasst", "next_player_id": nxt}
    
    # If game is complete, include completion data
    if is_complete:
        result["game_complete"] = True
        result["completion_data"] = completion_data
    
    return result

@router.post("/{game_id}/complete")
def complete_game(game_id: str,
                 db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    """Manually complete a game and calculate final scores."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Spiel nicht gefunden")
    
    # Check if user is a participant
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    if not player:
        raise HTTPException(403, "Du bist kein Teilnehmer dieses Spiels")
    
    # Finalize the game
    completion_data = finalize_game(game_id, db)
    
    return {
        "message": "Spiel beendet",
        "completion_data": completion_data
    }

@router.get("/{game_id}/language")
def get_game_language(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Get the language used for a game."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Spiel nicht gefunden")
    
    # Get language from game state
    state = json.loads(game.state)
    language = state.get("language", "de")  # Default to German if not specified
    
    return {"language": language}

@router.post("/{game_id}/language")
def set_game_language(
    game_id: str,
    language: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Set the language for a game."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Spiel nicht gefunden")
    
    # Check if user is a participant
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    if not player:
        raise HTTPException(403, "Du bist kein Teilnehmer dieses Spiels")
    
    # Check if game has already started
    if game.current_player_id:
        raise HTTPException(400, "Spiel bereits gestartet")
    
    # Ensure wordlist is available for this language
    if not ensure_wordlist_available(language, db):
        raise HTTPException(404, f"Sprache '{language}' nicht verfügbar")
    
    # Update game state with language
    state = json.loads(game.state)
    if isinstance(state, list):
        # Convert old format to new format
        state = {
            "board": state,
            "language": language
        }
    else:
        state["language"] = language
    
    game.state = json.dumps(state)
    db.commit()
    
    return {"language": language}
