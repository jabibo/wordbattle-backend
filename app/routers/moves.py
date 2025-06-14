from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Game, Move, Player
from pydantic import BaseModel, Field
from typing import List, Dict
import json
from datetime import datetime, timezone
from app.game_logic.board_utils import apply_move_to_board, BOARD_MULTIPLIERS
from app.game_logic.full_points import calculate_full_move_points, LETTER_POINTS
from app.game_logic.validate_move import validate_move
from app.auth import get_current_user
from app.game_logic.rules import get_next_player
from app.utils.wordlist_utils import load_wordlist
from app.websocket import manager
from app.game_logic.game_state import GameState
from app.routers.games import GameStateEncoder
from app.utils.logger import logger

router = APIRouter(prefix="/games/{game_id}")

class MoveLetter(BaseModel):
    row: int = Field(..., description="Row coordinate (0-14)")
    col: int = Field(..., description="Column coordinate (0-14)")
    letter: str = Field(..., min_length=1, max_length=1, description="Letter to place")

    def validate_coordinates(self):
        """Validate coordinates are within board bounds"""
        if not (0 <= self.row < 15 and 0 <= self.col < 15):
            raise ValueError("Invalid coordinates: must be between 0 and 14")
        return True

    def validate_letter(self):
        """Validate letter is valid"""
        if not self.letter.isalpha() and self.letter not in ('?', '*'):
            raise ValueError("Invalid letter")
        return self.letter.upper()

class MoveCreate(BaseModel):
    move_data: List[MoveLetter] = Field(..., min_items=1, description="List of letters to place")

@router.post("/move")
async def make_move(
    game_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Make a move in the game.
    
    Returns:
        400 for:
        - Invalid coordinates
        - Empty move data
        - Invalid game state
        - Invalid move (game rules)
        
        403 for:
        - Not your turn
        - Not in game
        
        404 for:
        - Game not found
    """
    # Get game from database
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=404,
            detail="Game not found"
        )
    
    # Check if game has started
    if not game.current_player_id:
        raise HTTPException(
            status_code=400,
            detail="Game has not started"
        )
    
    # Check if it's the player's turn
    if str(game.current_player_id) != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Not your turn"
        )
    
    # Get current player's rack
    player = db.query(Player).filter(
        Player.game_id == game_id,
        Player.user_id == current_user.id
    ).first()
    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )
    
    # Parse and validate move data
    try:
        body = await request.json()
        if not isinstance(body, dict) or "move_data" not in body:
            raise HTTPException(
                status_code=400,
                detail="Request body must be a JSON object with 'move_data' field"
            )
        
        move_data = body["move_data"]
        if not isinstance(move_data, list):
            raise HTTPException(
                status_code=400,
                detail="move_data must be a list"
            )
        
        if not move_data:
            raise HTTPException(
                status_code=400,
                detail="move_data cannot be empty"
            )
        
        # Validate each move item
        parsed_moves = []
        for item in move_data:
            if not isinstance(item, dict):
                raise HTTPException(
                    status_code=400,
                    detail="Each move item must be an object"
                )
            
            # Check required fields
            required_fields = ["row", "col", "letter"]
            for field in required_fields:
                if field not in item:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required field: {field}"
                    )
            
            # Validate field types
            if not isinstance(item["row"], int):
                raise HTTPException(
                    status_code=400,
                    detail="row must be an integer"
                )
            if not isinstance(item["col"], int):
                raise HTTPException(
                    status_code=400,
                    detail="col must be an integer"
                )
            if not isinstance(item["letter"], str):
                raise HTTPException(
                    status_code=400,
                    detail="letter must be a string"
                )
            
            # Validate coordinates
            if not (0 <= item["row"] < 15 and 0 <= item["col"] < 15):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid coordinates: must be between 0 and 14"
                )
            
            parsed_moves.append((item["row"], item["col"], item["letter"]))
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON"
        )
    
    # Load board state
    board = [[None for _ in range(15)] for _ in range(15)]
    moves = db.query(Move).filter(Move.game_id == game_id).all()
    for move in moves:
        move_data = json.loads(move.move_data)
        if isinstance(move_data, list):  # Handle old format
            for m in move_data:
                board[m["row"]][m["col"]] = m["letter"]
        else:  # Handle new format
            for m in move_data.get("move_data", []):
                board[m["row"]][m["col"]] = m["letter"]
    
    # Load dictionary
    try:
        dictionary = load_wordlist(game.language)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"Dictionary not found for language: {game.language}"
        )
    
    # Validate move
    is_valid, reason = validate_move(board, parsed_moves, list(player.rack), dictionary)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=reason
        )
    
    # Calculate points
    result = calculate_full_move_points(board, parsed_moves, LETTER_POINTS, BOARD_MULTIPLIERS, dictionary)
    if not result["valid"]:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )
    
    # Update board
    for row, col, letter in parsed_moves:
        board[row][col] = letter
    
    # Update player's rack and score
    used_letters = [letter for _, _, letter in parsed_moves]
    new_rack = list(player.rack)
    for letter in used_letters:
        if letter in new_rack:
            new_rack.remove(letter)
        elif "?" in new_rack:  # Handle blank tiles
            new_rack.remove("?")
    player.rack = "".join(new_rack)
    player.score += result["total"]
    
    # Record move
    move = Move(
        game_id=game_id,
        player_id=current_user.id,
        move_data=json.dumps({
            "move_data": [{"row": r, "col": c, "letter": l} for r, c, l in parsed_moves],
            "points": result["total"],
            "words": result["words"]
        }),
        timestamp=datetime.now(timezone.utc)
    )
    db.add(move)
    
    # Update current player
    next_player = get_next_player(game_id, current_user.id, db)
    game.current_player_id = next_player
    
    # Commit changes
    db.commit()
    
    # Notify websocket clients
    game_state = GameState.from_db(game_id, db)
    await manager.broadcast_game_update(game_id, game_state)
    
    return {
        "success": True,
        "points": result["total"],
        "words": result["words"],
        "details": result["details"]
    }

@router.post("/")
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
    
    return {"success": True, "message": "Move recorded"}
