# app/routers/games.py

from fastapi import APIRouter, Depends, HTTPException, Body, WebSocket, WebSocketDisconnect, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc, text, and_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json
import uuid
import logging
from datetime import datetime, timezone

from app.db import get_db
from app.dependencies import get_translation_helper
from app.models import Game, Player, Move, User, ChatMessage, GameInvitation
from app.models.game import GameStatus
from app.models.game_invitation import InvitationStatus
from app.auth import get_current_user, get_token_from_header, get_user_from_token
from app.game_logic.game_state import GameState, GamePhase, MoveType, Position, PlacedTile
from app.game_logic.letter_bag import LETTER_DISTRIBUTION, LetterBag, create_letter_bag, draw_letters, return_letters, create_rack
from app.utils.i18n import TranslationHelper
from app.utils.wordlist_utils import ensure_wordlist_available, load_wordlist
from app.utils.email_service import email_service
from app.utils.game_helpers import (
    get_player_data, get_last_move_info, get_next_player_info, 
    format_time_since_activity, get_game_summary_data, 
    get_detailed_game_data, sort_games_by_priority, group_games_by_status,
    is_computer_user_id as helper_is_computer_user_id
)
from app.config import FRONTEND_URL
from app.websocket import manager
from jose import JWTError, jwt
from app.auth import SECRET_KEY, ALGORITHM
import random
from app.game_logic.board_utils import find_word_placements
from app.game_logic.rules import get_next_player
from app.game_logic.board_utils import BOARD_MULTIPLIERS
import secrets
from app.utils.cache import cache_response
from app.computer_player import create_computer_player, add_computer_player_to_game

logger = logging.getLogger(__name__)

def is_computer_player(player, db):
    """Check if a player is a computer player."""
    if hasattr(player, 'user_id'):
        user = db.query(User).filter(User.id == player.user_id).first()
        return user and user.username == "computer_player"
    return False

def get_computer_user_id(db):
    """Get the computer player's user ID."""
    computer_user = db.query(User).filter(User.username == "computer_player").first()
    return computer_user.id if computer_user else None

# Use shared helper function for consistency
def is_computer_user_id(user_id, db):
    """Check if a user_id belongs to the computer player."""
    return helper_is_computer_user_id(user_id, db)

class CreateGameRequest(BaseModel):
    language: str = "en"
    max_players: int = 2
    short_game: bool = False  # Simple parameter for endgame testing
    add_computer_player: bool = False  # Add computer opponent during creation
    computer_difficulty: str = "medium"  # easy, medium, hard

class CreateGameContractRequest(BaseModel):
    name: str  # Required by contract
    language: str = "en"
    max_players: int = 2
    difficulty: Optional[str] = None  # easy, normal, hard
    time_limit: Optional[int] = None
    allow_challenges: Optional[bool] = None
    invitees: Optional[List[str]] = None
    add_computer_player: bool = False
    computer_difficulty: str = "medium"  # easy, medium, hard

class CreateGameWithInvitationsRequest(BaseModel):
    language: str = "en"
    max_players: int = 2
    invitees: List[str]  # List of usernames or email addresses to invite
    base_url: str = "http://localhost:3000"  # Default to frontend port
    short_game: bool = False  # Simple parameter for endgame testing
    add_computer_player: bool = False  # Add computer opponent during creation
    computer_difficulty: str = "medium"  # easy, medium, hard

class GameStateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (GamePhase, MoveType)):
            return obj.value
        elif isinstance(obj, Position):
            return {"row": obj.row, "col": obj.col}
        elif isinstance(obj, PlacedTile):
            return {"letter": obj.letter, "is_blank": obj.is_blank, "tile_id": obj.tile_id}
        elif isinstance(obj, set):
            return list(obj)
        return super().default(obj)

router = APIRouter(prefix="/games", tags=["games"])

def detect_center_used_from_board(board):
    """Helper function to detect if center has been used by checking if there's a tile at position (7,7)."""
    if not board or len(board) < 8 or len(board[7]) < 8:
        return False
    return board[7][7] is not None

def reconstruct_board_from_json(board_data):
    """Helper function to reconstruct board with proper PlacedTile objects from JSON data."""
    if not board_data:
        return [[None]*15 for _ in range(15)]
    
    reconstructed_board = []
    for row in board_data:
        reconstructed_row = []
        for cell in row:
            if cell is None:
                reconstructed_row.append(None)
            else:
                # Reconstruct PlacedTile object from JSON dict
                tile = PlacedTile(
                    letter=cell["letter"],
                    is_blank=cell.get("is_blank", False),
                    tile_id=cell.get("tile_id")  # Preserve existing tile_id or None (will auto-generate)
                )
                reconstructed_row.append(tile)
        reconstructed_board.append(reconstructed_row)
    return reconstructed_board

def format_game_state_response(game_data: dict, game_name: str) -> dict:
    """Format game data to match contract GameStateResponse schema."""
    # Transform players to contract format
    players = []
    player_info = game_data.get("players", {})
    
    for user_id, player in player_info.items():
        player_data = {
            "id": str(user_id),
            "username": player.get("username", "Unknown"),
            "score": player.get("score", 0),
            "is_current_player": str(user_id) == str(game_data.get("current_player_id")),
            "is_computer": player.get("is_computer", False)
        }
        
        # Include rack data if available (for current player or completed games)
        if "rack" in player and player["rack"]:
            player_data["rack"] = player["rack"]
        
        players.append(player_data)
    
    # Transform board to contract format (contract expects null or tile objects)
    board = game_data.get("board", [])
    contract_board = []
    for row in board:
        contract_row = []
        for cell in row:
            if cell is None:
                contract_row.append(None)
            else:
                # Convert our PlacedTile format to contract format
                contract_row.append({
                    "letter": cell.get("letter", ""),
                    "points": 1,  # Basic point value, could be calculated
                    "is_blank": cell.get("is_blank", False)
                })
        contract_board.append(contract_row)
    
    return {
        "id": game_data.get("id"),
        "name": game_name,  # Contract requires this
        "status": game_data.get("status"),
        "current_player_id": str(game_data.get("current_player_id")) if game_data.get("current_player_id") else None,
        "language": game_data.get("language"),
        "max_players": game_data.get("max_players"),
        "created_at": game_data.get("created_at"),
        "updated_at": game_data.get("started_at") or game_data.get("created_at"),  # Use started_at or created_at
        "players": players,
        "board": contract_board,
        "tiles_remaining": game_data.get("letter_bag_count", 0),
        "game_settings": {
            "time_limit": 0,  # Default values for optional contract fields
            "allow_challenges": True,
            "difficulty": "normal"
        }
    }

@router.post("/create")
def create_game_contract(
    game_data: CreateGameContractRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    t: TranslationHelper = Depends(get_translation_helper)
):
    """Create a new game (Contract-compliant endpoint)."""
    # Convert contract request to internal format
    internal_request = CreateGameRequest(
        language=game_data.language,
        max_players=game_data.max_players,
        short_game=False,  # Contract doesn't have this concept
        add_computer_player=game_data.add_computer_player,
        computer_difficulty=game_data.computer_difficulty
    )
    
    # Create the game using internal implementation
    game_response = create_game_impl(internal_request, db, current_user, t)
    
    # Get the complete game state
    game_id = game_response["id"]
    game_state_response = get_game(game_id, db, current_user)
    
    # The get_game function already returns formatted data with success field
    # Just update the name field to match the contract request
    if game_state_response.get("success"):
        game_state_response["name"] = game_data.name
    
    return game_state_response

def create_game_impl(
    game_data: CreateGameRequest,
    db: Session,
    current_user,
    t: TranslationHelper
):
    """Shared implementation for creating a new game."""
    # Validate language
    if game_data.language not in ["en", "de", "es", "fr", "it"]:
        raise HTTPException(400, t.error("invalid_language", languages="en, de, es, fr, it"))
    
    # Validate max_players
    if not (2 <= game_data.max_players <= 4):
        raise HTTPException(400, t.error("max_players_invalid"))
    
    # Ensure wordlist exists for the chosen language (or fallback to English for short games)
    if not ensure_wordlist_available(game_data.language, db):
        if game_data.short_game:
            # For short games (testing), fallback to English wordlist if target language not available
            logger.warning(f"⚠️  Wordlist for '{game_data.language}' not available, using English wordlist for short game testing")
            if not ensure_wordlist_available("en", db):
                raise HTTPException(500, t.error("wordlist_not_available", language="en (fallback)"))
        else:
            raise HTTPException(500, t.error("wordlist_not_available", language=game_data.language))
    
    # Create game record
    game = Game(
        id=str(uuid.uuid4()),
        creator_id=current_user.id,
        status=GameStatus.SETUP,
        language=game_data.language,
        max_players=game_data.max_players,
        created_at=datetime.now(timezone.utc)
    )
    
    # Initialize game state with short game mode if requested
    game_state = GameState(language=game_data.language, short_game=game_data.short_game)
    
    # Log short game creation for debugging
    if game_data.short_game:
        logger.info(f"🧪 SHORT GAME: Creating game {game.id} in short game mode with 24-tile letter bag for language {game_data.language}")
    
    initial_state = {
        "board": game_state.board,
        "phase": game_state.phase.value,
        "language": game_data.language,
        "multipliers": {f"{pos[0]},{pos[1]}": value for pos, value in game_state.multipliers.items()},
        "letter_bag": game_state.letter_bag,
        "turn_number": 0,
        "consecutive_passes": 0,
        "test_mode": game_data.short_game  # Store short_game flag as test_mode for backward compatibility
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
    
    # Add computer player if requested
    if game_data.add_computer_player:
        if game_data.computer_difficulty not in ["easy", "medium", "hard"]:
            raise HTTPException(400, "Invalid computer difficulty. Must be easy, medium, or hard")
        
        # Get computer user (created during startup)
        computer_user = db.query(User).filter(User.username == "computer_player").first()
        if not computer_user:
            raise HTTPException(500, "Computer player user not found. Please restart the service.")
        
        computer_player = Player(
            game_id=game.id,
            user_id=computer_user.id,
            score=0,
            rack=""  # Will be dealt when game starts
        )
        db.add(computer_player)
    
    db.commit()
    db.refresh(game)
    db.refresh(player)
    
    # Auto-start single-player computer games immediately
    if game_data.add_computer_player:
        logger.info(f"🤖 AUTO-START: Starting single-player computer game {game.id} immediately")
        
        # Get all players for the game
        all_players = db.query(Player).filter(Player.game_id == game.id).all()
        
        # Set game status to IN_PROGRESS
        game.status = GameStatus.IN_PROGRESS
        game.started_at = datetime.now(timezone.utc)
        
        # Set current player to the human player (they go first)
        game.current_player_id = current_user.id
        
        # Load current game state from DB JSON
        persisted_state_data = json.loads(game.state)
        game_state = GameState(language=game.language)
        game_state.board = reconstruct_board_from_json(persisted_state_data.get("board"))
        game_state.phase = GamePhase(persisted_state_data.get("phase", GamePhase.NOT_STARTED.value))
        
        # Reconstruct LetterBag object from persisted data
        letter_bag_data = persisted_state_data.get("letter_bag", [])
        if isinstance(letter_bag_data, dict) and "letters" in letter_bag_data:
            game_state.letter_bag = letter_bag_data["letters"]
        else:
            game_state.letter_bag = letter_bag_data
        
        game_state.turn_number = persisted_state_data.get("turn_number", 0)
        game_state.consecutive_passes = persisted_state_data.get("consecutive_passes", 0)
        
        # Deal initial racks to all players
        for player_obj in all_players:
            from app.game_logic.letter_bag import create_rack
            rack = create_rack(game_state.letter_bag)
            player_obj.rack = "".join(rack)
            logger.info(f"🎯 Dealt rack to player {player_obj.user_id}: {player_obj.rack}")
        
        # Update game state
        game_state.phase = GamePhase.IN_PROGRESS
        
        # Save updated game state back to DB
        updated_state_json = {
            "board": game_state.board,
            "phase": game_state.phase.value,
            "language": game.language,
            "multipliers": persisted_state_data.get("multipliers"),
            "letter_bag": game_state.letter_bag,
            "turn_number": game_state.turn_number,
            "consecutive_passes": game_state.consecutive_passes,
            "center_used": game_state.center_used
        }
        game.state = json.dumps(updated_state_json, cls=GameStateEncoder)
        
        db.commit()
        db.refresh(game)
        
        logger.info(f"✅ AUTO-START: Computer game {game.id} started. Human player goes first.")
    
    return {
        "id": game.id,
        "creator_id": game.creator_id,
        "status": game.status.value,
        "language": game.language,
        "max_players": game.max_players,
        "created_at": game.created_at.isoformat()
    }

@router.post("/")
def create_game(
    game_data: CreateGameRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    t: TranslationHelper = Depends(get_translation_helper)
):
    """Create a new game (original endpoint)."""
    return create_game_impl(game_data, db, current_user, t)

@router.get("/my")
def get_my_games_contract(
    status_filter: List[str] = Query(None, description="Filter games by status"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user's games (Contract-compliant endpoint) using shared helper functions."""
    # Get games using existing implementation
    games_response = list_user_games(status_filter, db, current_user)
    games = games_response.get("games", [])
    
    # Use shared helper function to group games by status
    return group_games_by_status(games)

@router.get("/available")
def get_available_games(
    language: Optional[str] = Query(None, description="Filter by game language"),
    max_players: Optional[int] = Query(None, description="Filter by max players"),
    limit: int = Query(10, description="Maximum number of games to return"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get available games that the user can join (Contract-compliant endpoint)."""
    # Find games that are joinable (SETUP or READY status) and not full
    query = db.query(Game).filter(
        Game.status.in_([GameStatus.SETUP, GameStatus.READY])
    )
    
    # Apply filters
    if language:
        query = query.filter(Game.language == language)
    if max_players:
        query = query.filter(Game.max_players == max_players)
    
    # Get games and check if they're joinable
    games = query.order_by(desc(Game.created_at)).limit(limit * 2).all()  # Get more to filter
    
    available_games = []
    for game in games:
        # Check if user is already in this game
        is_player = db.query(Player).filter(
            Player.game_id == game.id,
            Player.user_id == current_user.id
        ).first()
        
        if is_player:
            continue  # Skip games user is already in
        
        # Check if game is full
        current_players = db.query(Player).filter(Player.game_id == game.id).count()
        if current_players >= game.max_players:
            continue  # Skip full games
        
        # Get game creator info
        creator = db.query(User).filter(User.id == game.creator_id).first()
        
        # Format game info for contract response
        game_info = {
            "id": game.id,
            "name": f"Game by {creator.username if creator else 'Unknown'}",  # Contract requires name
            "status": game.status.value,
            "language": game.language,
            "max_players": game.max_players,
            "current_players": current_players,
            "created_at": game.created_at.isoformat(),
            "creator": {
                "id": str(game.creator_id),
                "username": creator.username if creator else "Unknown"
            },
            "can_join": True
        }
        
        available_games.append(game_info)
        
        # Stop when we have enough games
        if len(available_games) >= limit:
            break
    
    return {
        "available_games": available_games,
        "total_count": len(available_games),
        "filters": {
            "language": language,
            "max_players": max_players
        }
    }

@router.post("/create-with-invitations")
def create_game_with_invitations(
    game_data: CreateGameWithInvitationsRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new game with automatic invitations and email notifications."""
    # Validate language
    if game_data.language not in ["en", "de", "es", "fr", "it"]:
        raise HTTPException(400, "Invalid language. Supported languages: en, de, es, fr, it")
    
    # Validate max_players
    if not (2 <= game_data.max_players <= 4):
        raise HTTPException(400, "Max players must be between 2 and 4")
    
    # Validate invitees count
    if len(game_data.invitees) == 0:
        raise HTTPException(400, "At least one invitee is required")
    
    if len(game_data.invitees) >= game_data.max_players:
        raise HTTPException(400, f"Too many invitees. Maximum {game_data.max_players - 1} invitees for {game_data.max_players} player game")
    
    # Ensure wordlist exists for the chosen language (or fallback to English for short games)
    if not ensure_wordlist_available(game_data.language, db):
        if game_data.short_game:
            # For short games (testing), fallback to English wordlist if target language not available
            logger.warning(f"⚠️  Wordlist for '{game_data.language}' not available, using English wordlist for short game testing")
            if not ensure_wordlist_available("en", db):
                raise HTTPException(500, t.error("wordlist_not_available", language="en (fallback)"))
        else:
            raise HTTPException(500, t.error("wordlist_not_available", language=game_data.language))
    
    # Create game record
    game = Game(
        id=str(uuid.uuid4()),
        creator_id=current_user.id,
        status=GameStatus.SETUP,
        language=game_data.language,
        max_players=game_data.max_players,
        created_at=datetime.now(timezone.utc)
    )
    
    # Initialize game state with short game mode if requested
    game_state = GameState(language=game_data.language, short_game=game_data.short_game)
    
    # Log short game creation for debugging
    if game_data.short_game:
        logger.info(f"🧪 SHORT GAME: Creating game {game.id} in short game mode with 24-tile letter bag for language {game_data.language}")
    
    initial_state = {
        "board": game_state.board,
        "phase": game_state.phase.value,
        "language": game_data.language,
        "multipliers": {f"{pos[0]},{pos[1]}": value for pos, value in game_state.multipliers.items()},
        "letter_bag": game_state.letter_bag,
        "turn_number": 0,
        "consecutive_passes": 0,
        "test_mode": game_data.short_game  # Store short_game flag as test_mode for backward compatibility
    }
    game.state = json.dumps(initial_state, cls=GameStateEncoder)
    
    # Add creator as first player
    creator_player = Player(
        game_id=game.id,
        user_id=current_user.id,
        score=0,
        rack=""  # Will be dealt when game starts
    )
    
    db.add(game)
    db.add(creator_player)
    
    # Process invitations
    invitations_created = []
    invitations_sent = 0
    failed_invitations = []
    
    for invitee_identifier in game_data.invitees:
        # Try to find user by username first, then by email
        invitee = db.query(User).filter(
            (User.username == invitee_identifier) | (User.email == invitee_identifier)
        ).first()
        
        if not invitee:
            failed_invitations.append({
                "identifier": invitee_identifier,
                "reason": "User not found"
            })
            continue
        
        # Check if user is already the creator
        if invitee.id == current_user.id:
            failed_invitations.append({
                "identifier": invitee_identifier,
                "reason": "Cannot invite yourself"
            })
            continue
        
        # Generate secure join token
        join_token = secrets.token_urlsafe(32)
        
        # Create invitation
        invitation = GameInvitation(
            game_id=game.id,
            inviter_id=current_user.id,
            invitee_id=invitee.id,
            join_token=join_token,
            status=InvitationStatus.PENDING
        )
        
        db.add(invitation)
        invitations_created.append(invitation)
        
        # Send email invitation asynchronously (don't wait for email to complete)
        try:
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            # Send email in background - don't block game creation
            def send_email_background():
                try:
                    email_sent = email_service.send_game_invitation(
                        to_email=invitee.email,
                        invitee_username=invitee.username,
                        inviter_username=current_user.username,
                        game_id=game.id,
                        join_token=join_token,
                        base_url=game_data.base_url
                    )
                    if email_sent:
                        logger.info(f"✅ Email invitation sent successfully to {invitee.email}")
                    else:
                        logger.warning(f"⚠️ Email invitation failed for {invitee.email}")
                    return email_sent
                except Exception as e:
                    logger.error(f"❌ Email invitation error for {invitee.email}: {e}")
                    return False
            
            # Start email sending in background thread
            executor = ThreadPoolExecutor(max_workers=1)
            executor.submit(send_email_background)
            
            # Don't wait for email - assume it will be sent successfully (optimistic approach)
            invitations_sent += 1
            
        except Exception as e:
            logger.error(f"Email setup error for {invitee_identifier}: {e}")
            # Don't fail the invitation creation due to email issues
            invitations_sent += 1
    
    # Check if we have any valid invitations
    if len(invitations_created) == 0:
        db.rollback()
        raise HTTPException(400, f"No valid invitations could be created. Errors: {failed_invitations}")
    
    # Update game status to WAITING if we have invitations
    if len(invitations_created) > 0:
        game.status = GameStatus.SETUP  # Will change to READY when players accept
    
    db.commit()
    db.refresh(game)
    
    return {
        "id": game.id,
        "creator_id": game.creator_id,
        "status": game.status.value,
        "language": game.language,
        "max_players": game.max_players,
        "created_at": game.created_at.isoformat(),
        "invitations_created": len(invitations_created),
        "invitations_sent": invitations_sent,
        "failed_invitations": failed_invitations,
        "message": f"Game created with {len(invitations_created)} invitations. {invitations_sent} email(s) sent successfully."
    }

@router.post("/{game_id}/join")
async def join_game(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    t: TranslationHelper = Depends(get_translation_helper)
):
    """Join an existing game."""
    # Check if game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, t.error("game_not_found"))
    
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
        raise HTTPException(400, t.error("game_full"))
    
    # Add user as a player
    player = Player(
        game_id=game_id,
        user_id=current_user.id,
        score=0,
        rack=""  # Will be dealt when game starts
    )
    
    db.add(player)
    
    # Check for any pending invitations for this user and game and update their status
    pending_invitation = db.query(GameInvitation).filter(
        GameInvitation.game_id == game_id,
        GameInvitation.invitee_id == current_user.id,
        GameInvitation.status == InvitationStatus.PENDING
    ).first()
    
    if pending_invitation:
        # Update invitation status to accepted
        pending_invitation.status = InvitationStatus.ACCEPTED
        pending_invitation.responded_at = datetime.now(timezone.utc)
        
        # No longer creating friendships - removed friends system
    
    # Check if game should transition to READY state
    new_player_count = current_players + 1
    
    # Check if all invitations are responded to and we have enough players
    pending_invitations = db.query(GameInvitation).filter(
        GameInvitation.game_id == game_id,
        GameInvitation.status == InvitationStatus.PENDING
    ).count()
    
    if new_player_count >= 2 and (pending_invitations == 0 or new_player_count == game.max_players):
        # Auto-start the game immediately when all players have joined
        logger.info(f"🚀 AUTO-START: Game {game_id} is ready with {new_player_count} players. Starting automatically...")
        
        # Get all players for the game
        all_players = db.query(Player).filter(Player.game_id == game_id).all()
        
        # Get test mode from game state
        state_data = json.loads(game.state) if game.state else {}
        short_game = state_data.get("test_mode", False)
        
        # Create letter bag (use short game mode if enabled)
        from ..game_logic.letter_bag import create_letter_bag, create_rack
        import random
        
        letter_bag = create_letter_bag(game.language, short_game=short_game)
        
        # Log short game start for debugging
        if short_game:
            logger.info(f"🧪 SHORT GAME: Auto-starting game {game_id} in short game mode with {len(letter_bag)}-tile letter bag")
        
        # Deal initial letters to players
        for player in all_players:
            player.rack = create_rack(letter_bag)
        
        # Set game status and first player (randomly selected for fairness)
        game.status = GameStatus.IN_PROGRESS
        first_player = random.choice(all_players)
        game.current_player_id = first_player.user_id
        game.started_at = datetime.now(timezone.utc)
        
        logger.info(f"🎮 AUTO-START: Game {game_id} started with {len(all_players)} players. First player randomly selected: {first_player.user.username} (ID: {first_player.user_id})")
        
        # Update the game state JSON to reflect the started game
        state_data.update({
            "phase": GamePhase.IN_PROGRESS.value,
            "letter_bag": letter_bag,
            "turn_number": 0,
            "consecutive_passes": 0
        })
        game.state = json.dumps(state_data, cls=GameStateEncoder)
        
        # Notify via WebSocket that game has started
        try:
            await manager.broadcast_to_game(game_id, {
                "type": "game_started",
                "game_id": game_id,
                "current_player_id": game.current_player_id,
                "player_count": new_player_count,
                "message": f"🚀 Game started automatically! {new_player_count} players joined. {first_player.user.username} goes first!"
            })
        except Exception as e:
            logger.warning(f"WebSocket broadcast error after auto-start {game_id}: {e}")
    elif new_player_count >= 2 and game.status == GameStatus.SETUP:
        game.status = GameStatus.READY
    
    db.commit()
    db.refresh(player)
    db.refresh(game)
    
    return {
        "message": t.success("game_joined"),
        "game_id": game_id,
        "player_count": new_player_count,
        "game_status": game.status.value
    }

@router.post("/{game_id}/join-with-token")
async def join_game_with_token(
    game_id: str,
    token: str = Query(..., description="Join token from invitation email"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Join a game using a join token from an email invitation."""
    # Find the invitation by game_id and join_token
    invitation = db.query(GameInvitation).filter(
        GameInvitation.game_id == game_id,
        GameInvitation.join_token == token,
        GameInvitation.status == InvitationStatus.PENDING
    ).first()
    
    if not invitation:
        raise HTTPException(404, "Invalid or expired invitation token")
    
    # Check if the current user is the invited user
    if invitation.invitee_id != current_user.id:
        raise HTTPException(403, "This invitation is not for you")
    
    # Check if game exists and is in a joinable state
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    if game.status not in [GameStatus.SETUP, GameStatus.READY]:
        raise HTTPException(400, f"Cannot join game in {game.status.value} status")
    
    # Check if user is already a player
    existing_player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    if existing_player:
        # Update invitation status to accepted
        invitation.status = InvitationStatus.ACCEPTED
        invitation.responded_at = datetime.now(timezone.utc)
        db.commit()
        
        return {
            "message": "You are already a player in this game",
            "game_id": game_id,
            "game_status": game.status.value
        }
    
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
    
    # Update invitation status
    invitation.status = InvitationStatus.ACCEPTED
    invitation.responded_at = datetime.now(timezone.utc)
    
    # No longer creating friendships - removed friends system
    
    # Check if game should transition to READY state and auto-start
    new_player_count = current_players + 1
    
    # Check if all invitations are responded to and we have enough players
    pending_invitations = db.query(GameInvitation).filter(
        GameInvitation.game_id == game_id,
        GameInvitation.status == InvitationStatus.PENDING
    ).count()
    
    if new_player_count >= 2 and (pending_invitations == 0 or new_player_count == game.max_players):
        # Auto-start the game immediately when all players have joined
        logger.info(f"🚀 AUTO-START: Game {game_id} is ready with {new_player_count} players. Starting automatically...")
        
        # Get all players for the game
        all_players = db.query(Player).filter(Player.game_id == game_id).all()
        
        # Get test mode from game state
        state_data = json.loads(game.state) if game.state else {}
        short_game = state_data.get("test_mode", False)
        
        # Create letter bag (use short game mode if enabled)
        from ..game_logic.letter_bag import create_letter_bag, create_rack
        import random
        
        letter_bag = create_letter_bag(game.language, short_game=short_game)
        
        # Log short game start for debugging
        if short_game:
            logger.info(f"🧪 SHORT GAME: Auto-starting game {game_id} in short game mode with {len(letter_bag)}-tile letter bag")
        
        # Deal initial letters to players
        for player in all_players:
            player.rack = create_rack(letter_bag)
        
        # Set game status and first player (randomly selected for fairness)
        game.status = GameStatus.IN_PROGRESS
        first_player = random.choice(all_players)
        game.current_player_id = first_player.user_id
        game.started_at = datetime.now(timezone.utc)
        
        logger.info(f"🎮 AUTO-START: Game {game_id} started with {len(all_players)} players. First player randomly selected: {first_player.user.username} (ID: {first_player.user_id})")
        
        # Update the game state JSON to reflect the started game
        state_data.update({
            "phase": GamePhase.IN_PROGRESS.value,
            "letter_bag": letter_bag,
            "turn_number": 0,
            "consecutive_passes": 0
        })
        game.state = json.dumps(state_data, cls=GameStateEncoder)
        
        # Notify via WebSocket that game has started
        try:
            await manager.broadcast_to_game(game_id, {
                "type": "game_started",
                "game_id": game_id,
                "current_player_id": game.current_player_id,
                "player_count": new_player_count,
                "message": f"🚀 Game started automatically! {new_player_count} players joined. {first_player.user.username} goes first!"
            })
        except Exception as e:
            logger.warning(f"WebSocket broadcast error after auto-start {game_id}: {e}")
    
    db.commit()
    db.refresh(player)
    db.refresh(game)
    
    return {
        "message": "Successfully joined the game via invitation",
        "game_id": game_id,
        "player_count": new_player_count,
        "game_status": game.status.value,
        "invitation_accepted": True
    }

@router.get("/my-games")
def list_user_games(
    status_filter: List[str] = Query(None, description="Filter games by status. Valid values: setup, ready, in_progress, completed, cancelled. If not provided, shows all games."),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all games the current user participates in using shared helper functions.
    
    Args:
        status_filter: List of game statuses to include. Valid values: 
                      - "setup": Games being set up, waiting for invitations
                      - "ready": All players accepted, waiting to start  
                      - "in_progress": Games currently being played
                      - "completed": Finished games
                      - "cancelled": Cancelled games
                      If not provided, shows all games.
    """
    
    # Optimized query with eager loading to prevent N+1 queries
    query = db.query(Game).join(Player).filter(
        Player.user_id == current_user.id
    ).options(
        selectinload(Game.players).joinedload(Player.user)
    )
    
    # Add filter for specific statuses if requested
    if status_filter and len(status_filter) > 0:  # Show all games if None or empty list
        # Validate status values
        valid_statuses = ["setup", "ready", "in_progress", "completed", "cancelled"]
        invalid_statuses = [s for s in status_filter if s not in valid_statuses]
        if invalid_statuses:
            raise HTTPException(400, f"Invalid status values: {invalid_statuses}. Valid values: {valid_statuses}")
        
        # Convert string values to GameStatus enum values for filtering
        status_enums = []
        for status_str in status_filter:
            if status_str == "setup":
                status_enums.append(GameStatus.SETUP)
            elif status_str == "ready":
                status_enums.append(GameStatus.READY)
            elif status_str == "in_progress":
                status_enums.append(GameStatus.IN_PROGRESS)
            elif status_str == "completed":
                status_enums.append(GameStatus.COMPLETED)
            elif status_str == "cancelled":
                status_enums.append(GameStatus.CANCELLED)
        
        query = query.filter(Game.status.in_(status_enums))
    # If status_filter is None or empty, no filtering is applied (shows all games)
    
    user_games = query.all()

    # Use shared helper function to get game summary data
    games_info = []
    for game in user_games:
        game_summary = get_game_summary_data(game, current_user.id, db)
        games_info.append(game_summary)
    
    # Sort games using shared helper function
    games_info = sort_games_by_priority(games_info)
    
    return {
        "success": True,
        "games": games_info,
        "total_games": len(games_info),
        "games_waiting_for_user": sum(1 for g in games_info if g["is_user_turn"]),
        "active_games": sum(1 for g in games_info if g["status"] == "in_progress"),
        "completed_games": sum(1 for g in games_info if g["status"] == "completed")
    }

@router.get("/my-invitations")
def get_my_invitations(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all pending invitations for the current user."""
    invitations = db.query(GameInvitation).filter(
        and_(
            GameInvitation.invitee_id == current_user.id,
            GameInvitation.status == InvitationStatus.PENDING
        )
    ).all()
    
    invitation_list = []
    for inv in invitations:
        invitation_list.append({
            "invitation_id": inv.id,
            "game_id": inv.game_id,
            "inviter": {
                "id": str(inv.inviter.id),  # Convert to string per contract
                "username": inv.inviter.username,
                "email": inv.inviter.email
            },
            "game": {
                "id": inv.game.id,
                "language": inv.game.language,
                "max_players": inv.game.max_players,
                "status": inv.game.status.value,
                "created_at": inv.game.created_at.isoformat()
            },
            "status": inv.status.value,
            "created_at": inv.created_at.isoformat(),
            "join_token": inv.join_token
        })
    
    return {
        "invitations": invitation_list,
        "total_count": len(invitation_list),
        "pending_count": len([inv for inv in invitation_list if inv["status"] == "pending"])
    }

# Friends system removed - see /profile/me/previous-players instead

@router.get("/{game_id}")
def get_game(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) # Assuming this verifies user is part of game or admin
):
    """Get detailed game information using shared helper functions."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    # Check if current_user is part of this game
    is_player = db.query(Player).filter(Player.game_id == game_id, Player.user_id == current_user.id).first()
    if not is_player and game.creator_id != current_user.id:
         # Add admin check here if needed, e.g. if current_user.is_admin:
        raise HTTPException(403, "You are not part of this game.")

    # Use shared helper function to get detailed game data
    game_data = get_detailed_game_data(game, current_user.id, db)

    # Format according to contract and wrap in success field
    formatted_response = format_game_state_response(game_data, "WordBattle Game")
    return {"success": True, **formatted_response}

@router.get("/{game_id}/state")
def get_game_state(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get detailed game state including player racks and board state."""
    # Use the existing get_game function but return the raw data without success wrapper
    game_response = get_game(game_id, db, current_user)
    
    # Remove the success wrapper if it exists
    if isinstance(game_response, dict) and "success" in game_response:
        # Extract the actual game data
        game_data = {k: v for k, v in game_response.items() if k != "success"}
        return game_data
    
    return game_response

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
    
    # Get test mode from game state
    state_data = json.loads(game.state) if game.state else {}
    short_game = state_data.get("test_mode", False)  # Keep "test_mode" key for backward compatibility
    
    # Create letter bag (use short game mode if enabled)
    letter_bag = create_letter_bag(game.language, short_game=short_game)
    
    # Log short game start for debugging
    if short_game:
        logger.info(f"🧪 SHORT GAME: Starting game {game_id} in short game mode with {len(letter_bag)}-tile letter bag")
    
    # Deal initial letters to players
    for player in players:
        player.rack = create_rack(letter_bag)
    
    # Set game status and first player (randomly selected for fairness)
    game.status = GameStatus.IN_PROGRESS
    first_player = random.choice(players)
    game.current_player_id = first_player.user_id
    game.started_at = datetime.now(timezone.utc)
    
    logger.info(f"Game {game_id} started with {len(players)} players. First player randomly selected: {first_player.user.username} (ID: {first_player.user_id})")
    
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
    move_data: List[dict], # [{"row": int, "col": int, "letter": str, "is_blank": bool (optional), "tile_id": str (optional)}]
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
    game_state.board = reconstruct_board_from_json(persisted_state_data.get("board"))
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
    # Restore center_used flag from persisted state, or detect from board if not available
    if "center_used" in persisted_state_data:
        game_state.center_used = persisted_state_data["center_used"]
    else:
        # Fallback for existing games: detect if center is used by checking the board
        game_state.center_used = detect_center_used_from_board(game_state.board)

    # Load player racks and scores from Player table into GameState
    db_players = db.query(Player).filter(Player.game_id == game_id).all()
    for p_rec in db_players:
        game_state.players[p_rec.user_id] = p_rec.rack 
        game_state.scores[p_rec.user_id] = p_rec.score      

    # Defensive: Ensure current user is in game_state.players and has a rack
    if current_user.id not in game_state.players:
        logger.error(f"Player {current_user.id} not found in game {game_id} players: {list(game_state.players.keys())}")
        raise HTTPException(403, "You are not a player in this game.")
    if not isinstance(game_state.players[current_user.id], str) or not game_state.players[current_user.id]:
        logger.error(f"Player {current_user.id} has no rack in game {game_id}. Players: {game_state.players}")
        raise HTTPException(500, "Player rack is missing or invalid.")

    # Convert move_data from API (list of dicts) to GameState format (list of tuples)
    parsed_move_positions = []
    for m_item in move_data:
        try:
            pos = Position(m_item["row"], m_item["col"])
            tile = PlacedTile(
                letter=m_item["letter"], 
                is_blank=m_item.get("is_blank", False),
                tile_id=m_item.get("tile_id")  # Use provided tile_id or None (will auto-generate)
            )
            parsed_move_positions.append((pos, tile))
        except KeyError: # pragma: no cover
            logger.error(f"Invalid move data: {m_item}")
            raise HTTPException(400, "Invalid move data format. Each item must have 'row', 'col', 'letter'.")

    logger.info(f"Player {current_user.id} making move in game {game_id}: {parsed_move_positions}, rack: {game_state.players[current_user.id]}")

    # Load dictionary for word validation
    try:
        dictionary = load_wordlist(game.language)
    except FileNotFoundError: # pragma: no cover
        raise HTTPException(500, f"Wordlist for language '{game.language}' not found.")
    
    # Execute the move logic within GameState
    try:
        success, message, points_gained = game_state.make_move(
            current_user.id,
            MoveType.PLACE,
            parsed_move_positions,
            dictionary
        )
    except Exception as e:
        logger.error(f"Error in make_move logic: {e}")
        raise HTTPException(500, f"Internal error during move: {e}")
    
    if not success:
        raise HTTPException(400, message) # Move was invalid
    
    # Get detailed score breakdown for this move
    logger.info(f"🔍 Getting detailed score breakdown for move with {len(parsed_move_positions)} positions")
    try:
        score_breakdown = game_state.calculate_detailed_score_breakdown(parsed_move_positions)
        logger.info(f"🔍 Score breakdown calculated successfully: {score_breakdown}")
    except Exception as e:
        logger.error(f"🔍 Error calculating score breakdown: {e}")
        score_breakdown = None
    
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


    # Persist updated GameState to game.state JSON
    updated_state_json = {
        "board": game_state.board,
        "phase": game_state.phase.value,
        "language": game.language, # Unchanged
        "multipliers": persisted_state_data.get("multipliers"), # Unchanged by move
        "letter_bag": game_state.letter_bag,
        "turn_number": game_state.turn_number,
        "consecutive_passes": game_state.consecutive_passes,
        "center_used": game_state.center_used,  # Include center_used flag
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
        "game_over": is_game_over,
        "score_breakdown": score_breakdown if score_breakdown else {"error": "Score breakdown calculation failed"}
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
                "points": points_gained,
                "score_breakdown": score_breakdown
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

@router.post("/{game_id}/test-move")
async def test_move(
    game_id: str,
    move_data: List[dict], # [{"row": int, "col": int, "letter": str, "is_blank": bool (optional), "tile_id": str (optional)}]
    skip_turn_validation: bool = Body(False, description="Skip turn validation for testing purposes"),
    skip_rack_validation: bool = Body(False, description="Skip rack validation for testing purposes"),
    test_rack: Optional[str] = Body(None, description="Override player's rack for testing (e.g., 'ABCDEFG'). If not provided, uses current rack."),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    🧪 TEST ENDPOINT: Make a move for testing purposes with optional validation bypasses.
    
    This endpoint allows developers to test moves using the player's current rack and game state.
    It can optionally bypass validations for testing edge cases:
    - It's not their turn (skip_turn_validation=true)
    - They don't have the required letters (skip_rack_validation=true) 
    - Using a custom rack for testing (test_rack="ABCDEFG")
    
    By default, it uses the player's current rack and actual game state for realistic testing.
    
    ⚠️ WARNING: This is for development/testing only and should not be used in production games!
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(400, f"Game is not in progress. Status: {game.status.value}")
        
    # Turn validation can be skipped for testing
    if not skip_turn_validation and game.current_player_id != current_user.id:
        raise HTTPException(403, "Not your turn (use skip_turn_validation=true to bypass for testing)")

    # Load game state from DB JSON (game.state)
    persisted_state_data = json.loads(game.state)
    game_state = GameState(language=game.language)
    game_state.board = reconstruct_board_from_json(persisted_state_data.get("board"))
    game_state.phase = GamePhase(persisted_state_data.get("phase", GamePhase.IN_PROGRESS.value))
    game_state.current_player_id = game.current_player_id
    
    # Reconstruct LetterBag object from persisted data
    letter_bag_data = persisted_state_data.get("letter_bag", [])
    if isinstance(letter_bag_data, dict) and "letters" in letter_bag_data:
        game_state.letter_bag = letter_bag_data["letters"]
    else:
        game_state.letter_bag = letter_bag_data
    
    game_state.turn_number = persisted_state_data.get("turn_number", 0)
    game_state.consecutive_passes = persisted_state_data.get("consecutive_passes", 0)
    
    if "center_used" in persisted_state_data:
        game_state.center_used = persisted_state_data["center_used"]
    else:
        game_state.center_used = detect_center_used_from_board(game_state.board)

    # Load player racks and scores from Player table into GameState
    db_players = db.query(Player).filter(Player.game_id == game_id).all()
    for p_rec in db_players:
        game_state.players[p_rec.user_id] = p_rec.rack 
        game_state.scores[p_rec.user_id] = p_rec.score
    
    # Get the player's current rack
    current_player_record = None
    for p_rec in db_players:
        if p_rec.user_id == current_user.id:
            current_player_record = p_rec
            break
    
    if not current_player_record:
        raise HTTPException(404, "Player not found in game")
    
    original_rack = current_player_record.rack
    
    # Override rack for testing if provided, otherwise use current rack
    if test_rack:
        game_state.players[current_user.id] = test_rack
        logger.info(f"🧪 TEST MODE: Using test rack '{test_rack}' for user {current_user.id}")
        rack_source = "custom test rack"
    else:
        # Use the player's actual current rack
        logger.info(f"🧪 TEST MODE: Using current rack '{original_rack}' for user {current_user.id}")
        rack_source = "current player rack"
    
    # Convert move_data to GameState format
    parsed_move_positions = []
    for m_item in move_data:
        try:
            pos = Position(m_item["row"], m_item["col"])
            tile = PlacedTile(
                letter=m_item["letter"], 
                is_blank=m_item.get("is_blank", False),
                tile_id=m_item.get("tile_id")
            )
            parsed_move_positions.append((pos, tile))
        except KeyError:
            raise HTTPException(400, "Invalid move data format. Each item must have 'row', 'col', 'letter'.")

    # Load dictionary for word validation
    try:
        dictionary = load_wordlist(game.language)
    except FileNotFoundError:
        raise HTTPException(500, f"Wordlist for language '{game.language}' not found.")
    
    # Temporarily disable rack validation if requested
    if skip_rack_validation:
        # Save original rack validation method
        original_validate_rack = game_state._validate_rack_usage
        # Replace with a method that always returns True
        game_state._validate_rack_usage = lambda *args, **kwargs: (True, "Rack validation bypassed for testing")
        logger.info(f"🧪 TEST MODE: Rack validation bypassed for user {current_user.id}")
    
    try:
        # Execute the move logic within GameState
        success, message, points_gained = game_state.make_move(
            current_user.id,
            MoveType.PLACE,
            parsed_move_positions,
            dictionary,
            skip_turn_validation=skip_turn_validation  # Pass the skip flag to GameState
        )
    finally:
        # Restore original rack validation if it was disabled
        if skip_rack_validation:
            game_state._validate_rack_usage = original_validate_rack
    
    if not success:
        raise HTTPException(400, f"Move validation failed: {message}")
    
    # Get detailed score breakdown for this test move
    logger.info(f"🔍 Getting detailed score breakdown for move with {len(parsed_move_positions)} positions")
    try:
        score_breakdown = game_state.calculate_detailed_score_breakdown(parsed_move_positions)
        logger.info(f"🔍 Score breakdown calculated successfully: {score_breakdown}")
    except Exception as e:
        logger.error(f"🔍 Error calculating score breakdown: {e}")
        score_breakdown = None
    
    # Prepare response with test results
    response_data = {
        "test_mode": True,
        "message": f"TEST MOVE SUCCESS: {message}",
        "points_gained": points_gained,
        "move_valid": success,
        "score_breakdown": score_breakdown,
        "original_rack": list(original_rack),
        "rack_used_for_test": list(game_state.players[current_user.id]),
        "rack_after_move": list(game_state.players[current_user.id]),
        "next_player_id": game_state.current_player_id,
        "turn_validation_skipped": skip_turn_validation,
        "rack_validation_skipped": skip_rack_validation,
        "rack_source": rack_source,
        "database_updated": False,  # Test moves don't update DB by default
        "warning": "This is a test move and does not affect the actual game state",
        "game_state": {
            "turn_number": game_state.turn_number,
            "letter_bag_count": len(game_state.letter_bag),
            "board_after_move": game_state.board,
            "scores_after_move": game_state.scores
        }
    }
    
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
    game_state.board = reconstruct_board_from_json(persisted_state_data.get("board"))
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
    # Restore center_used flag from persisted state, or detect from board if not available
    if "center_used" in persisted_state_data:
        game_state.center_used = persisted_state_data["center_used"]
    else:
        # Fallback for existing games: detect if center is used by checking the board
        game_state.center_used = detect_center_used_from_board(game_state.board)

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
        "center_used": game_state.center_used,  # Include center_used flag
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
    game_state.board = reconstruct_board_from_json(persisted_state_data.get("board"))
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
    # Restore center_used flag from persisted state, or detect from board if not available
    if "center_used" in persisted_state_data:
        game_state.center_used = persisted_state_data["center_used"]
    else:
        # Fallback for existing games: detect if center is used by checking the board
        game_state.center_used = detect_center_used_from_board(game_state.board)

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
        "center_used": game_state.center_used,  # Include center_used flag
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
        await manager.broadcast_to_game(game_id, broadcast_payload)
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

@router.get("/{game_id}/invitations")
def get_game_invitations(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all invitations for a game (only for game creator)."""
    # Check if game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    # Check if user is the creator
    if game.creator_id != current_user.id:
        raise HTTPException(403, "Only the game creator can view invitations")
    
    # Get all invitations for this game
    invitations = db.query(GameInvitation).filter(
        GameInvitation.game_id == game_id
    ).all()
    
    invitation_list = []
    for inv in invitations:
        invitation_list.append({
            "invitation_id": inv.id,
            "game_id": inv.game_id,
            "inviter": {
                "id": str(inv.inviter.id),  # Convert to string per contract
                "username": inv.inviter.username,
                "email": inv.inviter.email
            },
            "game": {
                "id": inv.game.id,
                "language": inv.game.language,
                "max_players": inv.game.max_players,
                "status": inv.game.status.value,
                "created_at": inv.game.created_at.isoformat()
            },
            "status": inv.status.value,
            "created_at": inv.created_at.isoformat(),
            "join_token": inv.join_token
        })
    
    return {
        "game_id": game_id,
        "invitations": invitation_list,
        "total_invitations": len(invitation_list),
        "pending_count": len([inv for inv in invitation_list if inv["status"] == "pending"]),
        "accepted_count": len([inv for inv in invitation_list if inv["status"] == "accepted"]),
        "declined_count": len([inv for inv in invitation_list if inv["status"] == "declined"])
    }

@router.post("/{game_id}/auto-start")
async def auto_start_game(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Auto-start a game when enough players have joined."""
    # Get game from database
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    # Check if user is the creator
    if game.creator_id != current_user.id:
        raise HTTPException(403, "Only the game creator can auto-start the game")
    
    # Check if game is in READY state
    if game.status != GameStatus.READY:
        raise HTTPException(400, f"Game cannot be auto-started. Current status: {game.status.value}")
    
    # Get all players
    players = db.query(Player).filter(Player.game_id == game_id).all()
    if len(players) < 2:
        raise HTTPException(400, "Not enough players to start game")
    
    # Get test mode from game state
    state_data = json.loads(game.state) if game.state else {}
    short_game = state_data.get("test_mode", False)  # Keep "test_mode" key for backward compatibility
    
    # Create letter bag (use short game mode if enabled)
    letter_bag = create_letter_bag(game.language, short_game=short_game)
    
    # Log short game start for debugging
    if short_game:
        logger.info(f"🧪 SHORT GAME: Starting game {game_id} in short game mode with {len(letter_bag)}-tile letter bag")
    
    # Deal initial letters to players
    for player in players:
        player.rack = create_rack(letter_bag)
    
    # Set game status and first player (randomly selected for fairness)
    game.status = GameStatus.IN_PROGRESS
    first_player = random.choice(players)
    game.current_player_id = first_player.user_id
    game.started_at = datetime.now(timezone.utc)
    
    logger.info(f"Game {game_id} auto-started with {len(players)} players. First player randomly selected: {first_player.user.username} (ID: {first_player.user_id})")
    
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
            "type": "game_auto_started",
            "game_id": game_id,
            "current_player_id": game.current_player_id,
            "player_count": len(players),
            "message": f"Game auto-started with {len(players)} players!"
        })
    except Exception as e:
        logger.error(f"WebSocket broadcast error after auto-start {game_id}: {e}")
    
    return {
        "success": True,
        "message": f"Game auto-started with {len(players)} players",
        "current_player_id": game.current_player_id,
        "game_status": game.status.value
    }

@router.post("/{game_id}/invite-random-player")
def invite_random_player(
    game_id: str,
    request_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Send an invitation to a random existing player."""
    
    base_url = request_data.get("base_url", FRONTEND_URL)
    
    # Check if game exists and user is the creator
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    if game.creator_id != current_user.id:
        raise HTTPException(403, "Only the game creator can send invitations")
    
    if game.status not in [GameStatus.SETUP, GameStatus.READY]:
        raise HTTPException(400, f"Cannot send invitations for game in {game.status.value} status")
    
    # Get current players to exclude them
    current_players = db.query(Player).filter(Player.game_id == game_id).all()
    current_player_ids = [p.user_id for p in current_players]
    
    # Get users who already have pending invitations
    existing_invitations = db.query(GameInvitation).filter(
        GameInvitation.game_id == game_id,
        GameInvitation.status == InvitationStatus.PENDING
    ).all()
    invited_user_ids = [inv.invitee_id for inv in existing_invitations]
    
    # Exclude current user, current players, and already invited users
    excluded_ids = set(current_player_ids + invited_user_ids + [current_user.id])
    
    # Get random users who are not excluded and accept invites for this language
    # Filter by invitation preferences
    potential_users = db.query(User).filter(
        ~User.id.in_(excluded_ids),
        User.allow_invites == True,  # User accepts invites
        User.preferred_languages.contains([game.language])  # User wants invites for this language
    ).all()
    
    if not potential_users:
        raise HTTPException(400, "No available users to invite")
    
    # Prefer users who have played games recently
    active_users = []
    inactive_users = []
    
    for user in potential_users:
        user_games = db.query(Player).filter(Player.user_id == user.id).count()
        if user_games > 0:
            active_users.append(user)
        else:
            inactive_users.append(user)
    
    # Select randomly from active users first, then inactive
    if active_users:
        selected_user = random.choice(active_users)
    else:
        selected_user = random.choice(inactive_users)
    
    # Generate join token
    join_token = secrets.token_urlsafe(32)
    
    # Create invitation
    invitation = GameInvitation(
        game_id=game_id,
        inviter_id=current_user.id,
        invitee_id=selected_user.id,
        join_token=join_token,
        status=InvitationStatus.PENDING
    )
    
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    # Send email invitation
    email_sent = email_service.send_random_player_invitation(
        to_email=selected_user.email,
        invitee_username=selected_user.username,
        inviter_username=current_user.username,
        game_id=game_id,
        join_token=join_token,
        base_url=base_url
    )
    
    logger.info(f"Random invitation sent to user {selected_user.id} for game {game_id}, email_sent: {email_sent}")
    
    return {
        "message": f"Random invitation sent to {selected_user.username}",
        "invitee": {
            "id": selected_user.id,
            "username": selected_user.username,
            "email": selected_user.email
        },
        "invitation_id": invitation.id,
        "join_token": join_token,
        "email_sent": email_sent,
        "game_id": game_id
    }

@router.post("/{game_id}/invite-user")
def invite_user_by_username(
    game_id: str,
    username: str = Body(..., description="Username to invite"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Invite a user by username to join the game."""
    
    # Check if game exists and user is the creator
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    if game.creator_id != current_user.id:
        raise HTTPException(403, "Only the game creator can send invitations")
    
    if game.status not in [GameStatus.SETUP, GameStatus.READY]:
        raise HTTPException(400, f"Cannot send invitations for game in {game.status.value} status")
    
    # Find user by username
    invitee = db.query(User).filter(User.username == username).first()
    if not invitee:
        raise HTTPException(404, f"User '{username}' not found")
    
    # Check if user accepts invites
    if not invitee.allow_invites:
        raise HTTPException(400, f"User '{username}' doesn't accept game invitations")
    
    # Check if user wants invites for this language
    if game.language not in (invitee.preferred_languages or ["en", "de"]):
        raise HTTPException(400, f"User '{username}' doesn't accept invites for '{game.language}' language")
    
    # Check if user is already in the game
    existing_player = db.query(Player).filter(
        Player.game_id == game_id,
        Player.user_id == invitee.id
    ).first()
    if existing_player:
        raise HTTPException(400, f"User '{username}' is already in this game")
    
    # Check if user already has a pending invitation
    existing_invitation = db.query(GameInvitation).filter(
        GameInvitation.game_id == game_id,
        GameInvitation.invitee_id == invitee.id,
        GameInvitation.status == InvitationStatus.PENDING
    ).first()
    if existing_invitation:
        raise HTTPException(400, f"User '{username}' already has a pending invitation for this game")
    
    # Check game capacity
    current_players = db.query(Player).filter(Player.game_id == game_id).count()
    pending_invitations = db.query(GameInvitation).filter(
        GameInvitation.game_id == game_id,
        GameInvitation.status == InvitationStatus.PENDING
    ).count()
    
    if current_players + pending_invitations >= game.max_players:
        raise HTTPException(400, "Game is full")
    
    # Generate join token
    join_token = secrets.token_urlsafe(32)
    
    # Create invitation
    invitation = GameInvitation(
        game_id=game_id,
        inviter_id=current_user.id,
        invitee_id=invitee.id,
        join_token=join_token,
        status=InvitationStatus.PENDING
    )
    
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    logger.info(f"Username-based invitation sent to {username} (ID: {invitee.id}) for game {game_id}")
    
    return {
        "message": f"Invitation sent to {username}",
        "invitee": {
            "id": invitee.id,
            "username": invitee.username
        },
        "invitation_id": invitation.id,
        "join_token": join_token,
        "game_id": game_id
    }

@router.get("/search-users")
def search_users_for_invitation(
    username_query: str = Query(..., description="Username to search for"),
    language: str = Query(None, description="Filter by users who accept invites for this language"),
    limit: int = Query(10, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Search for users by username who can be invited to games."""
    
    # Build base query for users who accept invites
    query = db.query(User).filter(
        User.allow_invites == True,
        User.username.ilike(f"%{username_query}%"),  # Case-insensitive search
        User.id != current_user.id  # Exclude current user
    )
    
    # Filter by language preference if specified
    if language:
        query = query.filter(User.preferred_languages.contains([language]))
    
    # Limit results
    users = query.limit(limit).all()
    
    # Format results
    results = []
    for user in users:
        results.append({
            "id": user.id,
            "username": user.username,
            "preferred_languages": user.preferred_languages or ["en", "de"],
            "last_login": user.last_login.isoformat() if user.last_login else None
        })
    
    return {
        "users": results,
        "total_found": len(results),
        "query": username_query,
        "language_filter": language
    }


# Computer Player Endpoints

class AddComputerPlayerRequest(BaseModel):
    difficulty: str = "medium"  # easy, medium, hard

@router.post("/{game_id}/add-computer-player")
def add_computer_player_endpoint(
    game_id: str,
    request: AddComputerPlayerRequest = AddComputerPlayerRequest(),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add a computer player to the game."""
    
    # Validate difficulty
    if request.difficulty not in ["easy", "medium", "hard"]:
        raise HTTPException(400, "Invalid difficulty. Must be 'easy', 'medium', or 'hard'")
    
    # Check if game exists and user is the creator
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    if game.creator_id != current_user.id:
        raise HTTPException(403, "Only the game creator can add computer players")
    
    if game.status != GameStatus.SETUP:
        raise HTTPException(400, f"Can only add computer players during game setup, current status: {game.status.value}")
    
    # Check if there's already a computer player
    computer_user_id = get_computer_user_id(db)
    existing_computer = db.query(Player).filter(
        Player.game_id == game_id,
        Player.user_id == computer_user_id
    ).first() if computer_user_id else None
    if existing_computer:
        raise HTTPException(400, "Game already has a computer player")
    
    # Check if there's room for another player
    current_players = db.query(Player).filter(Player.game_id == game_id).count()
    if current_players >= game.max_players:
        raise HTTPException(400, "Game is already full")
    
    try:
        # Add computer player to game
        computer_info = add_computer_player_to_game(game_id, db, request.difficulty)
        
        logger.info(f"Computer player added to game {game_id} with difficulty {request.difficulty}")
        
        return {
            "message": f"Computer player added with {request.difficulty} difficulty",
            "computer_player": computer_info,
            "game_id": game_id
        }
        
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to add computer player to game {game_id}: {e}")
        raise HTTPException(500, "Failed to add computer player")


@router.post("/{game_id}/computer-move")
async def trigger_computer_move(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Trigger a computer player move (for testing or manual triggering)."""
    
    # Get game
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    # Check if user is part of the game
    user_player = db.query(Player).filter(
        Player.game_id == game_id,
        Player.user_id == current_user.id
    ).first()
    if not user_player:
        raise HTTPException(403, "You are not part of this game")
    
    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(400, f"Game is not in progress, current status: {game.status.value}")
    
    # Check if it's the computer player's turn
    computer_user_id = get_computer_user_id(db)
    if game.current_player_id != computer_user_id:
        raise HTTPException(400, "It's not the computer player's turn")
    
    # Get computer player
    computer_player = db.query(Player).filter(
        Player.game_id == game_id,
        Player.user_id == computer_user_id
    ).first() if computer_user_id else None
    if not computer_player:
        raise HTTPException(400, "No computer player in this game")
    
    try:
        # Parse game state
        game_state_data = json.loads(game.state)
        
        # Load wordlist for the game language
        wordlist = load_wordlist(game.language)
        if not wordlist:
            raise HTTPException(500, f"Wordlist not available for language {game.language}")
        
        # Convert Set to List for computer player
        wordlist_list = list(wordlist)
        
        # Create computer player instance
        computer = create_computer_player("medium")  # Default to medium difficulty
        
        # Log rack information for debugging
        logger.info(f"Computer player rack: '{computer_player.rack}' (length: {len(computer_player.rack)})")
        
        # Make computer move
        move_result = computer.make_move(
            game_state_data=game_state_data,
            rack=computer_player.rack,
            wordlist=wordlist_list,
            db=db
        )
        
        if move_result["type"] == "pass":
            # Computer is passing
            # Update game state for pass
            game_state_data["consecutive_passes"] = game_state_data.get("consecutive_passes", 0) + 1
            game_state_data["turn_number"] = game_state_data.get("turn_number", 0) + 1
            
            # Move to next player
            all_players = db.query(Player).filter(Player.game_id == game_id).all()
            player_ids = [p.user_id for p in all_players]
            next_player_id = get_next_player(player_ids, game.current_player_id)
            game.current_player_id = next_player_id
            
            # Create pass move record
            move = Move(
                game_id=game_id,
                player_id=computer_player.user_id,
                move_data=json.dumps({"type": "PASS", "action": "pass", "points": 0}),
                timestamp=datetime.now(timezone.utc)
            )
            db.add(move)
            
        else:
            # Computer placed tiles
            tiles_data = move_result.get("tiles", [])
            
            # Update board in game state
            for tile in tiles_data:
                game_state_data["board"][tile["row"]][tile["col"]] = {
                    "letter": tile["letter"],
                    "is_blank": False,
                    "tile_id": f"comp_{uuid.uuid4().hex[:8]}"
                }
            
            # Update computer player's rack (remove used letters)
            rack_letters = list(computer_player.rack)
            for tile in tiles_data:
                if tile["letter"] in rack_letters:
                    rack_letters.remove(tile["letter"])
            
            # Draw new letters to fill rack
            letter_bag = game_state_data.get("letter_bag", [])
            if len(letter_bag) > 0:
                new_letters = draw_letters(letter_bag, 7 - len(rack_letters))
                rack_letters.extend(new_letters)
                # Update the letter bag in game state
                game_state_data["letter_bag"] = letter_bag
            computer_player.rack = "".join(rack_letters)
            
            # Update score
            computer_player.score += move_result.get("score", 0)
            
            # Reset consecutive passes
            game_state_data["consecutive_passes"] = 0
            game_state_data["turn_number"] = game_state_data.get("turn_number", 0) + 1
            
            # Move to next player
            all_players = db.query(Player).filter(Player.game_id == game_id).all()
            player_ids = [p.user_id for p in all_players]
            next_player_id = get_next_player(player_ids, game.current_player_id)
            game.current_player_id = next_player_id
            
            # Create move record
            move = Move(
                game_id=game_id,
                player_id=computer_player.user_id,
                move_data=json.dumps({
                    "type": "PLACE", 
                    "data": tiles_data, 
                    "points": move_result.get("score", 0),
                    "word": move_result.get("word", ""),
                    "rack_after": computer_player.rack
                }),
                timestamp=datetime.now(timezone.utc)
            )
            db.add(move)
        
        # Update game state
        game.state = json.dumps(game_state_data, cls=GameStateEncoder)
        
        db.commit()
        
        # Notify via WebSocket
        await manager.broadcast_to_game(game_id, {
            "type": "computer_move",
            "move": move_result,
            "next_player_id": game.current_player_id,
            "game_state": game_state_data
        })
        
        logger.info(f"Computer player made move in game {game_id}: {move_result['type']}")
        
        return {
            "message": f"Computer player {move_result['type']}",
            "move": move_result,
            "next_player_id": game.current_player_id,
            "computer_score": computer_player.score
        }
        
    except Exception as e:
        logger.error(f"Computer move failed in game {game_id}: {e}")
        db.rollback()
        raise HTTPException(500, f"Computer move failed: {str(e)}")


@router.get("/{game_id}/computer-player-info")
def get_computer_player_info(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get information about the computer player in the game."""
    
    # Check if user is part of the game
    user_player = db.query(Player).filter(
        Player.game_id == game_id,
        Player.user_id == current_user.id
    ).first()
    if not user_player:
        raise HTTPException(403, "You are not part of this game")
    
    # Get computer player
    computer_user_id = get_computer_user_id(db)
    computer_player = db.query(Player).filter(
        Player.game_id == game_id,
        Player.user_id == computer_user_id
    ).first() if computer_user_id else None
    
    if not computer_player:
        return {
            "has_computer_player": False,
            "message": "No computer player in this game"
        }
    
    return {
        "has_computer_player": True,
        "computer_player": {
            "id": computer_player.id,
            "user_id": computer_user_id,
            "username": "Computer",
            "display_name": "Computer Player",
            "score": computer_player.score,
            "is_computer": True
        }
    }

@router.post("/{game_id}/computer-move-debug")
async def debug_computer_move(
    game_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Debug endpoint to understand why computer AI is failing."""
    
    # Get game
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    # Check if user is part of the game
    user_player = db.query(Player).filter(
        Player.game_id == game_id,
        Player.user_id == current_user.id
    ).first()
    if not user_player:
        raise HTTPException(403, "You are not part of this game")
    
    # Get computer player
    computer_user_id = get_computer_user_id(db)
    computer_player = db.query(Player).filter(
        Player.game_id == game_id,
        Player.user_id == computer_user_id
    ).first() if computer_user_id else None
    
    if not computer_player:
        return {"error": "No computer player in this game"}
    
    try:
        # Parse game state
        game_state_data = json.loads(game.state)
        
        # Load wordlist for the game language
        wordlist = load_wordlist(game.language)
        wordlist_list = list(wordlist)
        
        # Create computer player instance
        computer = create_computer_player("medium")
        
        # Debug information
        debug_info = {
            "game_id": game_id,
            "language": game.language,
            "computer_rack": computer_player.rack,
            "rack_letters": list(computer_player.rack),
            "wordlist_size": len(wordlist_list),
            "board_tiles": 0,
            "sample_words": wordlist_list[:10] if wordlist_list else [],
            "can_make_words": [],
            "placement_tests": []
        }
        
        # Count board tiles
        board = game_state_data.get("board", [])
        for row in board:
            for cell in row:
                if cell is not None:
                    debug_info["board_tiles"] += 1
        
        # Test if computer can make some basic words
        test_words = ["KRAFT", "FAKT", "TRAF", "MELS", "MESS", "LESE"]
        rack_letters = list(computer_player.rack)
        
        for word in test_words:
            if word in wordlist_list:
                can_make = computer._can_make_word(word, rack_letters)
                debug_info["can_make_words"].append({
                    "word": word,
                    "can_make": can_make,
                    "in_wordlist": True
                })
            else:
                debug_info["can_make_words"].append({
                    "word": word,
                    "can_make": False,
                    "in_wordlist": False
                })
        
        # Test placement logic for words we can make
        for word_info in debug_info["can_make_words"]:
            if word_info["can_make"]:
                word = word_info["word"]
                placements = computer._find_word_placements_on_board(board, word, rack_letters)
                debug_info["placement_tests"].append({
                    "word": word,
                    "placements_found": len(placements),
                    "placements": placements[:3] if placements else []  # First 3 placements
                })
        
        # Try the actual move generation
        try:
            possible_moves = computer._find_possible_moves(board, rack_letters, wordlist_list)
            debug_info["possible_moves_count"] = len(possible_moves)
            debug_info["top_moves"] = possible_moves[:3] if possible_moves else []
        except Exception as e:
            debug_info["move_generation_error"] = str(e)
        
        return debug_info
        
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"}
