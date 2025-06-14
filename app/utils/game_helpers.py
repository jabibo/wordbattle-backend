"""
Game Helper Functions
Shared utilities for game endpoints to eliminate code duplication.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Game, Player, User, Move
from app.models.game import GameStatus
import json
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def is_computer_user_id(user_id: int, db: Session) -> bool:
    """Check if a user_id belongs to the computer player."""
    if user_id is None:
        return False
    user = db.query(User).filter(User.id == user_id).first()
    return user and user.username == "computer_player"

def get_player_data(player: Player, current_user_id: int, game_status: GameStatus, db: Session) -> Dict[str, Any]:
    """
    Single source of truth for player data formatting.
    This eliminates duplication between all game endpoints.
    
    Args:
        player: Player database object
        current_user_id: ID of the current user making the request
        game_status: Current status of the game
        db: Database session
        
    Returns:
        Formatted player data dictionary
    """
    player_user = db.query(User).filter(User.id == player.user_id).first()
    if not player_user:
        return None
    
    # Check if this is a computer player
    is_computer = is_computer_user_id(player.user_id, db)
    
    player_data = {
        "id": str(player_user.id),
        "username": "Computer" if is_computer else player_user.username,
        "score": player.score,
        "is_current_user": player_user.id == current_user_id,
        "is_computer": is_computer
    }
    
    # Unified rack visibility logic - fix once, works everywhere!
    show_rack = (
        player_user.id == current_user_id or      # Own rack
        game_status == GameStatus.COMPLETED or    # Game completed
        is_computer                               # Computer player (for debugging)
    ) and player.rack
    
    if show_rack:
        player_data["rack"] = list(player.rack)
    
    return player_data

def get_last_move_info(game_id: str, current_user_id: int, db: Session) -> Optional[Dict[str, Any]]:
    """
    Get formatted information about the last move in a game.
    
    Args:
        game_id: Game ID
        current_user_id: Current user ID
        db: Database session
        
    Returns:
        Formatted last move information or None
    """
    last_move = db.query(Move).filter(
        Move.game_id == game_id
    ).order_by(Move.timestamp.desc()).first()
    
    if not last_move:
        return None
    
    last_move_player = db.query(User).filter(User.id == last_move.player_id).first()
    if not last_move_player:
        return None
    
    try:
        move_data = json.loads(last_move.move_data)
        move_type = move_data.get("type", "unknown")
        
        # Format move description based on type
        if move_type == "word_placement":
            words = move_data.get("words_formed", [])
            move_description = f"Played word(s): {', '.join(words)}" if words else "Placed tiles"
        elif move_type == "pass":
            move_description = "Passed turn"
        elif move_type == "exchange":
            letters_count = len(move_data.get("letters_exchanged", []))
            move_description = f"Exchanged {letters_count} letter(s)"
        else:
            move_description = f"Made a {move_type} move"
    except (json.JSONDecodeError, KeyError):
        move_description = "Made a move"
    
    return {
        "player_id": str(last_move_player.id),
        "player_username": last_move_player.username,
        "timestamp": last_move.timestamp.isoformat(),
        "description": move_description,
        "was_current_user": last_move_player.id == current_user_id
    }

def get_next_player_info(game: Game, current_user_id: int, db: Session) -> Optional[Dict[str, Any]]:
    """
    Get information about the next player in a game.
    
    Args:
        game: Game object
        current_user_id: Current user ID
        db: Database session
        
    Returns:
        Next player information or None
    """
    if game.status != GameStatus.IN_PROGRESS or not game.current_player_id:
        return None
    
    next_player = db.query(User).filter(User.id == game.current_player_id).first()
    if not next_player:
        return None
    
    return {
        "id": str(next_player.id),
        "username": next_player.username,
        "is_current_user": next_player.id == current_user_id
    }

def format_time_since_activity(last_activity: datetime) -> str:
    """
    Format time since last activity in a human-readable way.
    
    Args:
        last_activity: Datetime of last activity
        
    Returns:
        Formatted time string
    """
    time_since_activity = datetime.now(timezone.utc) - last_activity.replace(tzinfo=timezone.utc)
    
    if time_since_activity.days > 0:
        return f"{time_since_activity.days} day(s) ago"
    elif time_since_activity.seconds > 3600:
        hours = time_since_activity.seconds // 3600
        return f"{hours} hour(s) ago"
    elif time_since_activity.seconds > 60:
        minutes = time_since_activity.seconds // 60
        return f"{minutes} minute(s) ago"
    else:
        return "Just now"

def get_game_summary_data(game: Game, current_user_id: int, db: Session) -> Dict[str, Any]:
    """
    Shared function to get game summary data for list views.
    Used by my-games and contract endpoints.
    
    Args:
        game: Game object
        current_user_id: Current user ID
        db: Database session
        
    Returns:
        Formatted game summary data
    """
    # Get all players
    players = db.query(Player).filter(Player.game_id == game.id).all()
    
    # Parse game state
    state_data = json.loads(game.state) if game.state else {}
    
    # Format players using shared function
    players_info = []
    for player in players:
        player_data = get_player_data(player, current_user_id, game.status, db)
        if player_data:
            # Add game-specific fields for list view
            player_data["is_creator"] = player.user_id == game.creator_id
            players_info.append(player_data)
    
    # Get additional info using shared functions
    next_player_info = get_next_player_info(game, current_user_id, db)
    last_move_info = get_last_move_info(game.id, current_user_id, db)
    
    # Calculate time since last activity
    last_move = db.query(Move).filter(Move.game_id == game.id).order_by(Move.timestamp.desc()).first()
    last_activity = last_move.timestamp if last_move else game.created_at
    time_since_str = format_time_since_activity(last_activity)
    
    return {
        "id": game.id,
        "status": game.status.value,
        "language": game.language,
        "max_players": game.max_players,
        "current_players": len(players),
        "created_at": game.created_at.isoformat(),
        "started_at": game.started_at.isoformat() if game.started_at else None,
        "completed_at": game.completed_at.isoformat() if game.completed_at else None,
        "current_player_id": str(game.current_player_id) if game.current_player_id else None,
        "turn_number": state_data.get("turn_number", 0),
        "is_user_turn": (game.status == GameStatus.IN_PROGRESS and game.current_player_id == current_user_id),
        "time_since_last_activity": time_since_str,
        "next_player": next_player_info,
        "last_move": last_move_info,
        "players": players_info,
        "user_score": next((p["score"] for p in players_info if p["is_current_user"]), 0)
    }

def get_detailed_game_data(game: Game, current_user_id: int, db: Session) -> Dict[str, Any]:
    """
    Shared function to get detailed game data for single game view.
    Used by get_game endpoint.
    
    Args:
        game: Game object
        current_user_id: Current user ID
        db: Database session
        
    Returns:
        Formatted detailed game data
    """
    state_data = json.loads(game.state) if game.state else {}
    
    # Get all players with detailed info
    players = db.query(Player).filter(Player.game_id == game.id).all()
    
    # DATA INTEGRITY CHECK: Verify current_player_id exists in players
    if game.current_player_id:
        player_ids = [p.user_id for p in players]
        if game.current_player_id not in player_ids:
            logger.error(f"🚨 DATA INTEGRITY ISSUE: Game {game.id} has current_player_id {game.current_player_id} but player not found in players {player_ids}")
            # Try to fix by setting current_player_id to first available player
            if players:
                game.current_player_id = players[0].user_id
                db.commit()
                logger.info(f"🔧 FIXED: Set current_player_id to {game.current_player_id}")
            else:
                # No players at all - this is a serious issue
                logger.error(f"🚨 CRITICAL: Game {game.id} has no players at all!")
                game.current_player_id = None
                db.commit()
    
    # Format players using shared function
    player_info = {}
    for player in players:
        player_data = get_player_data(player, current_user_id, game.status, db)
        if player_data:
            player_info[player.user_id] = player_data
    
    return {
        "id": game.id,
        "status": game.status.value,
        "language": game.language,
        "max_players": game.max_players,
        "created_at": game.created_at.isoformat(),
        "started_at": game.started_at.isoformat() if game.started_at else None,
        "current_player_id": game.current_player_id,
        "phase": state_data.get("phase"),
        "board": state_data.get("board"),
        "multipliers": state_data.get("multipliers"),
        "letter_bag_count": len(state_data.get("letter_bag", [])),
        "players": player_info,
        "turn_number": state_data.get("turn_number", 0),
        "consecutive_passes": state_data.get("consecutive_passes", 0)
    }

def sort_games_by_priority(games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort games by priority: user's turn first, then by last activity.
    
    Args:
        games: List of game data dictionaries
        
    Returns:
        Sorted list of games
    """
    def sort_key(game):
        if game["is_user_turn"]:
            return (0, game["created_at"])  # User's turn games first
        elif game["status"] == "in_progress":
            return (1, game["created_at"])  # Other in-progress games
        elif game["status"] == "ready":
            return (2, game["created_at"])  # Ready games
        elif game["status"] == "setup":
            return (3, game["created_at"])  # Setup games
        else:
            return (4, game["created_at"])  # Completed games last
    
    return sorted(games, key=sort_key, reverse=True)

def group_games_by_status(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Group games by status for contract-compliant format.
    
    Args:
        games: List of game data dictionaries
        
    Returns:
        Games grouped by status
    """
    active_games = []
    pending_games = []
    completed_games = []
    
    for game in games:
        status = game.get("status", "").lower()
        if status in ["in_progress"]:
            active_games.append(game)
        elif status in ["setup", "ready"]:
            pending_games.append(game)
        elif status in ["completed", "cancelled"]:
            completed_games.append(game)
        else:
            # Default to pending for unknown statuses
            pending_games.append(game)
    
    return {
        "active_games": active_games,
        "pending_games": pending_games,
        "completed_games": completed_games,
        "total_games": len(games)
    } 