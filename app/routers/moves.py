from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Game, Move, Player, WordList
from pydantic import BaseModel
from typing import List
import json
from datetime import datetime, timezone
from app.game_logic.board_utils import apply_move_to_board
from app.game_logic.full_points import calculate_full_move_points
from app.game_logic.validate_move import validate_move
from app.auth import get_current_user
from app.game_logic.rules import get_next_player
from app.wordlist import load_wordlist
from app.websocket import manager
from app.game_logic.game_state import GameState
from app.routers.games import GameStateEncoder
from app.utils.logger import logger

router = APIRouter(prefix="/games", tags=["moves"])

MULTIPLIERS = {
    (0, 0): "WW", (7, 7): "WW", (1, 5): "WL", (2, 2): "BL"
}

LETTER_POINTS = {
    'A': 1, 'B': 3, 'C': 4, 'D': 1, 'E': 1, 'F': 4, 'G': 2, 'H': 2, 'I': 1,
    'J': 6, 'K': 4, 'L': 2, 'M': 3, 'N': 1, 'O': 2, 'P': 4, 'Q': 10, 'R': 1,
    'S': 1, 'T': 1, 'U': 1, 'V': 6, 'W': 3, 'X': 8, 'Y': 10, 'Z': 3, '?': 0
}

class MoveLetter(BaseModel):
    row: int
    col: int
    letter: str

class MoveCreate(BaseModel):
    move_data: List[MoveLetter]

@router.post("/{game_id}/move")
async def make_move(game_id: str, move: MoveCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Spiel nicht gefunden")

    # Check if game has started
    if not game.current_player_id:
        raise HTTPException(status_code=400, detail="Spiel wurde noch nicht gestartet")

    # Check if it's the player's turn
    if game.current_player_id != current_user.id:
        raise HTTPException(status_code=403, detail="Nicht Dein Zug")

    # Check if player is in the game
    player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    if not player:
        raise HTTPException(status_code=403, detail="Du bist kein Teilnehmer dieses Spiels")

    # Parse game state
    state_data = json.loads(game.state)
    if isinstance(state_data, list):
        # Old format - just the board
        board = state_data
        language = "de"  # Default to German
    else:
        # New format - dictionary with board and language
        board = state_data.get("board", [[None]*15 for _ in range(15)])
        language = state_data.get("language", "de")

    move_tuples = [(m.row, m.col, m.letter) for m in move.move_data]

    # Get player's rack
    player_rack = list(player.rack)
    
    # Load dictionary for the game language
    DICTIONARY = load_wordlist(language)
    
    # Validate move
    is_valid, reason = validate_move(board, move_tuples, player_rack, DICTIONARY)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Ungültiger Zug: {reason}")

    result = calculate_full_move_points(board, move_tuples, LETTER_POINTS, MULTIPLIERS, DICTIONARY)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["error"])

    new_board = apply_move_to_board(board, move_tuples)
    
    # Update game state
    if isinstance(state_data, list):
        game.state = json.dumps(new_board)
    else:
        state_data["board"] = new_board
        game.state = json.dumps(state_data)

    # Get next player
    player_ids = [p.user_id for p in db.query(Player).filter(Player.game_id == game_id).order_by(Player.id)]
    next_player_id = get_next_player(player_ids, current_user.id)
    game.current_player_id = next_player_id

    db.add(game)

    move_entry = Move(
        game_id=game_id,
        player_id=current_user.id,
        move_data=json.dumps([m.model_dump() for m in move.move_data]),
        timestamp=datetime.now(timezone.utc)
    )
    db.add(move_entry)
    
    # Update player's rack and score
    used_letters = [letter for _, _, letter in move_tuples]
    rack_copy = player.rack
    for letter in used_letters:
        if letter in rack_copy:
            rack_copy = rack_copy.replace(letter, "", 1)
    
    player.rack = rack_copy
    player.score += result["total"]
    
    db.commit()
    
    # Check if the game is complete after this move
    from app.game_logic.game_completion import check_game_completion
    is_complete, completion_data = check_game_completion(game_id, db)
    
    response = {
        "message": "Zug erfolgreich",
        "points": result["total"],
        "words": result["words"],
        "new_state": new_board
    }
    
    # If game is complete, include completion data
    if is_complete:
        response["game_complete"] = True
        response["completion_data"] = completion_data
    
    # Broadcast game update via WebSocket
    try:
        await manager.broadcast_to_game(
            game_id,
            {
                "type": "game_update",
                "game_id": game_id,
                "state": new_board,
                "current_player_id": next_player_id,
                "last_move": {
                    "player_id": current_user.id,
                    "move_data": [m.model_dump() for m in move.move_data],
                    "points": result["total"],
                    "words": result["words"]
                }
            }
        )
    except Exception as e:
        logger.error(f"WebSocket broadcast error: {e}")
    
    return response

@router.post("/{game_id}")
async def record_move(
    game_id: str,
    move_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Record a move in the game."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    # Load game state
    state_data = json.loads(game.state)
    game_state = GameState()
    game_state.board = state_data.get("board", [[None]*15 for _ in range(15)])
    
    # Update game state
    state_data["board"] = game_state.board
    game.state = json.dumps(state_data, cls=GameStateEncoder)
    
    # Record move
    move = Move(
        game_id=game_id,
        player_id=current_user.id,
        move_data=json.dumps(move_data),
        timestamp=datetime.now(timezone.utc)
    )
    db.add(move)
    db.commit()
    
    return {"message": "Move recorded"}
