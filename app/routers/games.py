# app/routers/games.py

from fastapi import APIRouter, Depends, HTTPException, Body, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Game, Player, Move, User, ChatMessage
from app.models.game import GameStatus
from app.auth import get_current_user, get_token_from_header, get_user_from_token
from app.game_logic.game_state import GameState, GamePhase, MoveType, Position, PlacedTile
from app.game_logic.letter_bag import LETTER_DISTRIBUTION, LetterBag, create_letter_bag, draw_letters, return_letters, create_rack
from app.utils.wordlist_utils import ensure_wordlist_available, load_wordlist
import uuid
import json
from datetime import datetime, timezone
from app.websocket import manager
from typing import List, Optional, Dict, Any
from jose import JWTError, jwt
from app.auth import SECRET_KEY, ALGORITHM
import random
import logging
from app.game_logic.board_utils import find_word_placements
from pydantic import BaseModel
from app.game_logic.rules import get_next_player
from app.game_logic.board_utils import BOARD_MULTIPLIERS

logger = logging.getLogger(__name__)

class CreateGameRequest(BaseModel):
    language: str = "en"
    max_players: int = 2

class GameStateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (GamePhase, MoveType)):
            return obj.value
        elif isinstance(obj, Position):
            return {"row": obj.row, "col": obj.col}
        elif isinstance(obj, PlacedTile):
            return {"letter": obj.letter, "is_blank": obj.is_blank}
        elif isinstance(obj, set):
            return list(obj)
        return super().default(obj)

router = APIRouter(prefix="/games", tags=["games"])

@router.post("/")
def create_game(
    game_data: CreateGameRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new game."""
    # Validate language
    if game_data.language not in ["en", "de"]:
        raise HTTPException(400, "Invalid language. Supported languages: en, de")
    
    # Validate max_players
    if not (2 <= game_data.max_players <= 4):
        raise HTTPException(400, "Max players must be between 2 and 4")
    
    # Ensure wordlist exists for the chosen language
    if not ensure_wordlist_available(game_data.language, db):
        raise HTTPException(500, f"Wordlist for language '{game_data.language}' not available")
    
    # Create game record
    game = Game(
        id=str(uuid.uuid4()),
        creator_id=current_user.id,
        status=GameStatus.SETUP,
        language=game_data.language,
        max_players=game_data.max_players,
        created_at=datetime.now(timezone.utc)
    )
    
    # Initialize game state
    game_state = GameState(language=game_data.language)
    initial_state = {
        "board": game_state.board,
        "phase": game_state.phase.value,
        "language": game_data.language,
        "multipliers": {f"{pos[0]},{pos[1]}": value for pos, value in game_state.multipliers.items()},
        "letter_bag": game_state.letter_bag,
        "turn_number": 0,
        "consecutive_passes": 0
    }
    game.state = json.dumps(initial_state, cls=GameStateEncoder)
    
    # Add creator as first player
    player = Player(
        game_id=game.id,
        user_id=current_user.id,
        score=0,
        rack=""  # Will be dealt when game starts
    )
    
    db.add(game)
    db.add(player)
    db.commit()
    db.refresh(game)
    db.refresh(player)
    
    return {
        "id": game.id,
        "creator_id": game.creator_id,
        "status": game.status.value,
        "language": game.language,
        "max_players": game.max_players,
        "created_at": game.created_at.isoformat()
    }

@router.post("/{game_id}/join")
def join_game(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Join an existing game."""
    # Check if game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    # Check if game is in a joinable state
    if game.status not in [GameStatus.SETUP, GameStatus.READY]:
        raise HTTPException(400, f"Cannot join game in {game.status.value} status")
    
    # Check if user is already a player
    existing_player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    if existing_player:
        raise HTTPException(400, "You are already a player in this game")
    
    # Check if game is full
    current_players = db.query(Player).filter_by(game_id=game_id).count()
    if current_players >= game.max_players:
        raise HTTPException(400, "Game is full")
    
    # Add user as a player
    player = Player(
        game_id=game_id,
        user_id=current_user.id,
        score=0,
        rack=""  # Will be dealt when game starts
    )
    
    db.add(player)
    
    # Check if game should transition to READY state
    new_player_count = current_players + 1
    if new_player_count >= 2 and game.status == GameStatus.SETUP:
        game.status = GameStatus.READY
    
    db.commit()
    db.refresh(player)
    db.refresh(game)
    
    return {
        "message": "Successfully joined the game",
        "game_id": game_id,
        "player_count": new_player_count,
        "game_status": game.status.value
    }

@router.get("/{game_id}")
def get_game(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) # Assuming this verifies user is part of game or admin
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    # Check if current_user is part of this game
    is_player = db.query(Player).filter(Player.game_id == game_id, Player.user_id == current_user.id).first()
    if not is_player and game.creator_id != current_user.id:
         # Add admin check here if needed, e.g. if current_user.is_admin:
        raise HTTPException(403, "You are not part of this game.")

    state_data = json.loads(game.state)
    
    # Ensure player racks and scores are up-to-date from Player table if game is in progress or ready
    player_info = {}
    if game.status in [GameStatus.IN_PROGRESS, GameStatus.READY, GameStatus.COMPLETED]:
        db_players = db.query(Player).filter(Player.game_id == game_id).all()
        for p in db_players:
            player_info[p.user_id] = {
                "username": p.user.username, # Add username for better display
                "rack": list(p.rack) if (p.user_id == current_user.id or game.status == GameStatus.COMPLETED) and p.rack else [], # Only show own rack unless game over
                "score": p.score
            }
    
    # If game is in setup, invitees might be relevant, but players list from Player table is key
    if game.status == GameStatus.SETUP:
        db_players = db.query(Player).filter(Player.game_id == game_id).all() # Should only be creator initially
        for p in db_players:
             player_info[p.user_id] = {
                "username": p.user.username,
                "score": p.score # Score is 0 at setup
            }


    return {
        "id": game.id,
        "creator_id": game.creator_id,
        "status": game.status.value,
        "language": game.language,
        "max_players": game.max_players,
        "created_at": game.created_at.isoformat(),
        "started_at": game.started_at.isoformat() if game.started_at else None,
        "completed_at": game.completed_at.isoformat() if game.completed_at else None,
        "current_player_id": game.current_player_id,
        "phase": state_data.get("phase"), # Phase from game_state JSON
        "board": state_data.get("board"), # Board from game_state JSON
        "multipliers": state_data.get("multipliers"), # Multipliers from game_state JSON
        "letter_bag_count": len(state_data.get("letter_bag", [])) if "letter_bag" in state_data else LETTER_DISTRIBUTION.get(game.language, {}).get("total_tiles", 0), # Approx if not started
        "players": player_info, # Combined player data
        "turn_number": state_data.get("turn_number", 0),
        "consecutive_passes": state_data.get("consecutive_passes", 0)
    }

@router.post("/{game_id}/start")
async def start_game(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Start a game."""
    # Get game from database
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=404,
            detail="Game not found"
        )
    
    # Check if user is in game
    player = db.query(Player).filter(
        Player.game_id == game_id,
        Player.user_id == current_user.id
    ).first()
    if not player:
        raise HTTPException(
            status_code=403,
            detail="You are not part of this game"
        )
    
    # Check if game can be started
    if game.status != GameStatus.READY:
        raise HTTPException(
            status_code=400,
            detail="Game cannot be started"
        )
    
    # Get all players
    players = db.query(Player).filter(Player.game_id == game_id).all()
    if len(players) < 2:
        raise HTTPException(
            status_code=400,
            detail="Not enough players to start game"
        )
    
    # Create letter bag
    letter_bag = create_letter_bag(game.language)
    
    # Deal initial letters to players
    for player in players:
        player.rack = create_rack(letter_bag)
    
    # Set game status and first player
    game.status = GameStatus.IN_PROGRESS
    game.current_player_id = players[0].user_id
    game.started_at = datetime.now(timezone.utc)
    
    # Update the game state JSON to reflect the started game
    state_data = json.loads(game.state) if game.state else {}
    state_data.update({
        "phase": GamePhase.IN_PROGRESS.value,
        "letter_bag": letter_bag,
        "turn_number": 0,
        "consecutive_passes": 0
    })
    game.state = json.dumps(state_data, cls=GameStateEncoder)
    
    # Save changes
    db.commit()
    
    # Notify websocket clients about game start
    try:
        await manager.broadcast_to_game(game_id, {
            "type": "game_started",
            "game_id": game_id,
            "current_player_id": game.current_player_id,
            "message": "Game has started!"
        })
    except Exception as e:
        logger.error(f"WebSocket broadcast error after game start {game_id}: {e}")
    
    return {"success": True}

@router.post("/{game_id}/move")
async def make_move(
    game_id: str,
    move_data: List[dict], # [{"row": int, "col": int, "letter": str, "is_blank": bool (optional)}]
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(400, f"Game is not in progress. Status: {game.status.value}")
        
    if game.current_player_id != current_user.id:
        raise HTTPException(403, "Not your turn")

    # Load game state from DB JSON (game.state)
    persisted_state_data = json.loads(game.state)
    game_state = GameState(language=game.language)
    game_state.board = persisted_state_data.get("board", [[None]*15 for _ in range(15)])
    game_state.phase = GamePhase(persisted_state_data.get("phase", GamePhase.IN_PROGRESS.value)) # Default to IN_PROGRESS
    game_state.current_player_id = game.current_player_id # From Game table
    
    # Reconstruct LetterBag object from persisted data
    letter_bag_data = persisted_state_data.get("letter_bag", [])
    if isinstance(letter_bag_data, dict) and "letters" in letter_bag_data:
        # If it was serialized as a LetterBag object with letters attribute
        game_state.letter_bag = letter_bag_data["letters"]
    else:
        # If it was serialized as a simple list
        game_state.letter_bag = letter_bag_data
    
    game_state.turn_number = persisted_state_data.get("turn_number", 0)
    game_state.consecutive_passes = persisted_state_data.get("consecutive_passes", 0)

    # Load player racks and scores from Player table into GameState
    db_players = db.query(Player).filter(Player.game_id == game_id).all()
    for p_rec in db_players:
        game_state.players[p_rec.user_id] = p_rec.rack 
        game_state.scores[p_rec.user_id] = p_rec.score      
    
    # Convert move_data from API (list of dicts) to GameState format (list of tuples)
    parsed_move_positions = []
    for m_item in move_data:
        try:
            pos = Position(m_item["row"], m_item["col"])
            tile = PlacedTile(m_item["letter"], m_item.get("is_blank", False))
            parsed_move_positions.append((pos, tile))
        except KeyError: # pragma: no cover
            raise HTTPException(400, "Invalid move data format. Each item must have 'row', 'col', 'letter'.")

    # Load dictionary for word validation
    try:
        dictionary = load_wordlist(game.language)
    except FileNotFoundError: # pragma: no cover
        raise HTTPException(500, f"Wordlist for language '{game.language}' not found.")
    
    # Execute the move logic within GameState
    success, message, points_gained = game_state.make_move(
        current_user.id,
        MoveType.PLACE,
        parsed_move_positions,
        dictionary
    )
    
    if not success:
        raise HTTPException(400, message) # Move was invalid
    
    # Update Game table
    game.current_player_id = game_state.current_player_id # game_state updates this
    
    # Update Player records in DB (rack, score)
    for p_rec in db_players:
        p_rec.rack = "".join(game_state.players[p_rec.user_id])
        p_rec.score = game_state.scores[p_rec.user_id]
    
    # Record the move in Moves table
    move_entry = Move(
        game_id=game_id,
        player_id=current_user.id,
        move_data=json.dumps({"type": MoveType.PLACE.value, "data": move_data, "points": points_gained}), # Store move type, data, and points in JSON
        timestamp=datetime.now(timezone.utc)
    )
    db.add(move_entry)
    
    # Check for game completion
    is_game_over, completion_details = game_state.check_game_end() # This updates game_state.phase too
    
    if is_game_over:
        game.status = GameStatus.COMPLETED
        game.completed_at = datetime.now(timezone.utc)
        # Final scores are in game_state.scores, update Player table one last time
        for p_rec in db_players:
            p_rec.score = game_state.scores[p_rec.user_id]
            if game_state.bonus_points.get(p_rec.user_id, 0) != 0 : # If end game bonus applied
                 # Log or store bonus points if necessary, already included in p_rec.score by game_state
                 pass


    # Persist updated GameState to game.state JSON
    updated_state_json = {
        "board": game_state.board,
        "phase": game_state.phase.value,
        "language": game.language, # Unchanged
        "multipliers": persisted_state_data.get("multipliers"), # Unchanged by move
        "letter_bag": game_state.letter_bag,
        "turn_number": game_state.turn_number,
        "consecutive_passes": game_state.consecutive_passes,
        "player_racks_snapshot": {uid: list(rack) for uid, rack in game_state.players.items()}, # Snapshot current racks
        "player_scores_snapshot": game_state.scores.copy(), # Snapshot current scores
        "completion_data": completion_details if is_game_over else None
    }
    game.state = json.dumps(updated_state_json, cls=GameStateEncoder)
    
    db.commit()
    
    # Prepare HTTP response
    response_data = {
        "message": message,
        "points_gained": points_gained,
        "your_new_rack": list(game_state.players[current_user.id]),
        "next_player_id": game.current_player_id,
        "game_over": is_game_over
    }
    if is_game_over:
        response_data["completion_details"] = completion_details
    
    # Broadcast game update via WebSocket
    try:
        broadcast_payload = {
            "type": "game_update",
            "game_id": game_id,
            "board": game_state.board,
            "scores": {p.user_id: p.score for p in db_players}, # Fresh scores from DB
            "current_player_id": game.current_player_id,
            "last_move": {
                "player_id": current_user.id,
                "username": current_user.username,
                "move_data": move_data, # The move that was just made
                "points": points_gained
            },
            "game_over": is_game_over,
            "completion_details": completion_details if is_game_over else None,
            "letter_bag_count": len(game_state.letter_bag),
            "turn_number": game_state.turn_number,
            "consecutive_passes": game_state.consecutive_passes
        }
        await manager.broadcast_to_game(game.id, broadcast_payload)
    except Exception as e: # pragma: no cover
        logger.error(f"WebSocket broadcast error after move in game {game_id}: {e}")
    
    return response_data

@router.post("/{game_id}/pass")
async def pass_turn(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")

    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(400, f"Game is not in progress. Status: {game.status.value}")

    if game.current_player_id != current_user.id:
        raise HTTPException(403, "Not your turn")

    # Load game state
    persisted_state_data = json.loads(game.state)
    game_state = GameState(language=game.language)
    game_state.board = persisted_state_data.get("board", [[None]*15 for _ in range(15)])
    game_state.phase = GamePhase(persisted_state_data.get("phase", GamePhase.IN_PROGRESS.value))
    game_state.current_player_id = game.current_player_id
    
    # Reconstruct LetterBag object from persisted data
    letter_bag_data = persisted_state_data.get("letter_bag", [])
    if isinstance(letter_bag_data, dict) and "letters" in letter_bag_data:
        # If it was serialized as a LetterBag object with letters attribute
        game_state.letter_bag = letter_bag_data["letters"]
    else:
        # If it was serialized as a simple list
        game_state.letter_bag = letter_bag_data
    
    game_state.turn_number = persisted_state_data.get("turn_number", 0)
    game_state.consecutive_passes = persisted_state_data.get("consecutive_passes", 0)

    db_players = db.query(Player).filter(Player.game_id == game_id).all()
    for p_rec in db_players:
        game_state.players[p_rec.user_id] = p_rec.rack
        game_state.scores[p_rec.user_id] = p_rec.score
    
    # Make pass move
    success, message, _ = game_state.make_move( # No points for pass
        current_user.id,
        MoveType.PASS,
        [], # No move data for pass
        set()  # No dictionary needed
    )
    
    if not success: # pragma: no cover # Should always succeed for PASS if state is consistent
        raise HTTPException(400, message)
    
    # Update Game table
    game.current_player_id = game_state.current_player_id 
    
    # No change to Player records (rack, score) for a pass
    
    # Record pass action in Moves table
    move_entry = Move(
        game_id=game_id,
        player_id=current_user.id,
        move_data=json.dumps({"type": MoveType.PASS.value, "action": "pass", "points": 0}),
        timestamp=datetime.now(timezone.utc)
    )
    db.add(move_entry)
    
    # Check for game completion (e.g., too many consecutive passes)
    is_game_over, completion_details = game_state.check_game_end()
    if is_game_over:
        game.status = GameStatus.COMPLETED
        game.completed_at = datetime.now(timezone.utc)
        # Update final scores in Player table if check_game_end modified them (e.g. unplayed letters)
        for p_rec in db_players:
            p_rec.score = game_state.scores[p_rec.user_id]


    # Persist updated GameState to game.state JSON
    updated_state_json = {
        "board": game_state.board, # Unchanged by pass
        "phase": game_state.phase.value,
        "language": game.language,
        "multipliers": persisted_state_data.get("multipliers"),
        "letter_bag": game_state.letter_bag, # Unchanged by pass
        "turn_number": game_state.turn_number,
        "consecutive_passes": game_state.consecutive_passes, # Updated by make_move(PASS)
        "player_racks_snapshot": {uid: list(rack) for uid, rack in game_state.players.items()},
        "player_scores_snapshot": game_state.scores.copy(),
        "completion_data": completion_details if is_game_over else None
    }
    game.state = json.dumps(updated_state_json, cls=GameStateEncoder)

    db.commit()
    
    response_data = {
        "message": "Turn passed successfully.",
        "next_player_id": game.current_player_id,
        "game_over": is_game_over
    }
    if is_game_over:
        response_data["completion_details"] = completion_details
    
    # Broadcast game update
    try:
        broadcast_payload = {
            "type": "game_update",
            "game_id": game_id,
            "current_player_id": game.current_player_id,
            "last_action": {
                "type": MoveType.PASS.value,
                "player_id": current_user.id,
                "username": current_user.username,
            },
            "game_over": is_game_over,
            "completion_details": completion_details if is_game_over else None,
            "letter_bag_count": len(game_state.letter_bag),
            "turn_number": game_state.turn_number,
            "consecutive_passes": game_state.consecutive_passes,
            "scores": {p.user_id: p.score for p in db_players} # Scores don't change on pass, but good to send
        }
        await manager.broadcast_to_game(game.id, broadcast_payload)
    except Exception as e: # pragma: no cover
        logger.error(f"WebSocket broadcast error after pass in game {game_id}: {e}")
    
    return response_data

@router.post("/{game_id}/exchange")
async def exchange_letters(
    game_id: str,
    letters_to_exchange: List[str] = Body(..., embed=True),  # Explicitly expect {"letters_to_exchange": ["A", "B"]}
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")

    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(400, f"Game is not in progress. Status: {game.status.value}")

    if game.current_player_id != current_user.id:
        raise HTTPException(403, "Not your turn")

    if not letters_to_exchange:
        raise HTTPException(400, "No letters provided for exchange.")

    # Load game state
    persisted_state_data = json.loads(game.state)
    game_state = GameState(language=game.language)
    game_state.board = persisted_state_data.get("board") 
    game_state.phase = GamePhase(persisted_state_data.get("phase", GamePhase.IN_PROGRESS.value))
    game_state.current_player_id = game.current_player_id
    
    # Reconstruct LetterBag object from persisted data
    letter_bag_data = persisted_state_data.get("letter_bag", [])
    if isinstance(letter_bag_data, dict) and "letters" in letter_bag_data:
        # If it was serialized as a LetterBag object with letters attribute
        game_state.letter_bag = letter_bag_data["letters"]
    else:
        # If it was serialized as a simple list
        game_state.letter_bag = letter_bag_data
    
    game_state.turn_number = persisted_state_data.get("turn_number", 0)
    game_state.consecutive_passes = persisted_state_data.get("consecutive_passes", 0)

    db_players = db.query(Player).filter(Player.game_id == game_id).all()
    current_player_record = None
    for p_rec in db_players:
        game_state.players[p_rec.user_id] = p_rec.rack
        game_state.scores[p_rec.user_id] = p_rec.score # Scores don't change on exchange
        if p_rec.user_id == current_user.id:
            current_player_record = p_rec
            
    if not current_player_record: # Should not happen
        raise HTTPException(404, "Player not found in game")
    
    # Make exchange move
    success, message, new_rack_after_exchange = game_state.make_move(
        current_user.id,
        MoveType.EXCHANGE,
        letters_to_exchange, # Pass the list of letter strings
        set() 
    )
    
    if not success:
        raise HTTPException(400, message) # e.g., not enough letters in bag, letter not in rack
    
    # Update Game table
    game.current_player_id = game_state.current_player_id
    
    # Update player's rack in Player table
    current_player_record.rack = "".join(new_rack_after_exchange)
    
    # Record exchange action in Moves table
    move_entry = Move(
        game_id=game_id,
        player_id=current_user.id,
        move_data=json.dumps({"action": "exchange", "letters_exchanged_count": len(letters_to_exchange)}), # Don't log specific letters
        timestamp=datetime.now(timezone.utc)
    )
    db.add(move_entry)

    # No game end check needed specifically for exchange, but turn advances.
    # consecutive_passes is reset by game_state.make_move
    
    # Persist updated GameState to game.state JSON
    updated_state_json = {
        "board": game_state.board, # Unchanged
        "phase": game_state.phase.value, # Should remain IN_PROGRESS
        "language": game.language,
        "multipliers": persisted_state_data.get("multipliers"),
        "letter_bag": game_state.letter_bag, # Updated
        "turn_number": game_state.turn_number, # Updated
        "consecutive_passes": game_state.consecutive_passes, # Reset
        "player_racks_snapshot": {uid: list(rack) for uid, rack in game_state.players.items()},
        "player_scores_snapshot": game_state.scores.copy(),
        # No completion data from exchange
    }
    game.state = json.dumps(updated_state_json, cls=GameStateEncoder)
    
    db.commit()
    
    response_data = {
        "message": "Letters exchanged successfully.",
        "your_new_rack": list(new_rack_after_exchange),
        "next_player_id": game.current_player_id
    }
    
    # Broadcast game update
    try:
        broadcast_payload = {
            "type": "game_update",
            "game_id": game_id,
            "current_player_id": game.current_player_id,
            "last_action": {
                "type": MoveType.EXCHANGE.value,
                "player_id": current_user.id,
                "username": current_user.username,
                "exchange_count": len(letters_to_exchange) # Inform how many letters were exchanged
            },
            "letter_bag_count": len(game_state.letter_bag),
            "turn_number": game_state.turn_number,
            "consecutive_passes": game_state.consecutive_passes, # Will be 0
            "scores": {p.user_id: p.score for p in db_players} # Scores don't change
        }
        await manager.broadcast_to_game(game.id, broadcast_payload)
    except Exception as e: # pragma: no cover
        logger.error(f"WebSocket broadcast error after exchange in game {game_id}: {e}")
            
    return response_data

# This endpoint is likely DEPRECATED as dealing is part of move/exchange.
@router.post("/{game_id}/deal")
async def deal_letters( 
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """DEPRECATED: Dealing letters is now an integral part of game actions (move, exchange)
    and initial setup (/start). This endpoint should not be used for standard gameplay."""
    logger.warning(f"Deprecated /deal endpoint called for game {game_id} by user {current_user.username}")
    raise HTTPException(
        status_code=410, # Gone
        detail="Dealing letters is handled by other game actions (move, exchange, start). This endpoint is deprecated."
    )

# Helper to get User model from ID, could be in a utils or crud file
def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

@router.post("/{game_id}/validate_words")
async def validate_words(
    game_id: str,
    words: List[str] = Body(..., description="List of words to validate", example=["HELLO", "WORLD"]),
    include_placements: bool = Body(False, description="Whether to include possible placements for valid words"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Validate a list of words for a specific game's language and optionally find valid placements.
    This endpoint can be used by any authenticated user who is part of the game,
    regardless of whose turn it is.

    Parameters:
        game_id (str): The ID of the game whose language rules to use
        words (List[str]): List of words to validate
        include_placements (bool): Whether to include possible placements for valid words
        db (Session): Database session
        current_user (User): The authenticated user making the request

    Returns:
        dict: A dictionary containing validation results for each word and optional placement suggestions
    """
    # Check if game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    # Check if user is part of this game
    is_player = db.query(Player).filter(Player.game_id == game_id, Player.user_id == current_user.id).first()
    if not is_player and game.creator_id != current_user.id:
        raise HTTPException(403, "You are not part of this game")

    try:
        # Load dictionary for word validation
        dictionary = load_wordlist(game.language)
        
        # Get current game state if we need to find placements
        state_data = json.loads(game.state) if include_placements else None
        board = state_data.get("board", [[None]*15 for _ in range(15)]) if include_placements else None
        
        # Get player's rack if we need to find placements
        if include_placements:
            player = db.query(Player).filter(Player.game_id == game_id, Player.user_id == current_user.id).first()
            player_rack = list(player.rack) if player else []
        
        # Validate each word
        results = {}
        for word in words:
            # Convert to uppercase for consistency
            word = word.upper()
            # Check if word exists in dictionary
            is_valid = word in dictionary
            result = {
                "is_valid": is_valid,
                "reason": None if is_valid else "Word not found in dictionary"
            }
            
            # If word is valid and placements are requested, find possible placements
            if is_valid and include_placements:
                placements = find_word_placements(
                    board=board,
                    word=word,
                    player_rack=player_rack,
                    dictionary=dictionary,
                    is_first_move=(game.status == GameStatus.READY),
                    language=game.language  # Pass the game language for scoring
                )
                result["placements"] = placements
                if not placements:
                    result["placement_note"] = "No valid placements found with current rack and board state"
            
            results[word] = result
        
        return {
            "language": game.language,
            "validations": results
        }
        
    except FileNotFoundError:
        raise HTTPException(500, f"Wordlist for language '{game.language}' not found")
    except Exception as e:
        logger.error(f"Error validating words: {e}")
        raise HTTPException(500, "Error validating words")
