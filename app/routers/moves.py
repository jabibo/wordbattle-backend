from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Game, Move
from pydantic import BaseModel
from typing import List
import json
from datetime import datetime
from app.game_logic.board_utils import apply_move_to_board
from app.game_logic.full_points import calculate_full_move_points
from app.game_logic.validate_move import validate_move
from app.game_logic.rules import get_next_player

router = APIRouter(prefix="/games", tags=["moves"])

MULTIPLIERS = {
    (0, 0): "WW", (7, 7): "WW", (1, 5): "WL", (2, 2): "BL"
}

DICTIONARY = {"HALLO", "WELT", "DU", "ICH", "TAG", "TAGE", "TEST"}

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
def make_move(game_id: str, move: MoveCreate, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Spiel nicht gefunden")

    board = json.loads(game.state)
    move_tuples = [(m.row, m.col, m.letter) for m in move.move_data]

    player_rack = ["H", "A", "L", "L", "O", "T", "E"]  # TODO: aus DB laden
    is_valid, reason = validate_move(board, move_tuples, player_rack, DICTIONARY)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Ungültiger Zug: {reason}")

    result = calculate_full_move_points(board, move_tuples, LETTER_POINTS, MULTIPLIERS, DICTIONARY)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["error"])

    new_board = apply_move_to_board(board, move_tuples)
    game.state = json.dumps(new_board)

    if game.current_player_id and game.current_player_id != 1:
        raise HTTPException(status_code=403, detail="Du bist nicht am Zug")

    # Spielerrotation simulieren (TODO: Spielerliste aus DB)
    player_ids = [1, 2, 3]  # Beispielwerte
    next_player_id = get_next_player(player_ids, 1)
    game.current_player_id = next_player_id

    db.add(game)

    move_entry = Move(
        game_id=game_id,
        player_id=1,
        move_data=json.dumps([m.dict() for m in move.move_data]),
        timestamp=datetime.utcnow()
    )
    db.add(move_entry)
    # Punkte berechnen + Spielerpunkte erhöhen (simuliert)
    print(f"Punkte für Spieler 1: {result['total']}")
    # TODO: Punkte dem Spieler zuweisen
    db.commit()

    return {
        "message": "Zug erfolgreich",
        "points": result["total"],
        "words": result["words"],
        "new_state": new_board
    }
