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
    Legacy function for backward compatibility.
    
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

def get_last_move_summary(game_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Get last move summary matching the frontend contract requirements.
    
    Returns simplified last move information for easy frontend display:
    - player_username: Name of player who made the move
    - move_type: PLACE, PASS, or EXCHANGE
    - word: Word formed (for PLACE moves) or null
    - points_earned: Points earned from the move
    - timestamp: ISO timestamp of the move
    
    Args:
        game_id: Game ID
        db: Database session
        
    Returns:
        Last move summary or None if no moves made
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
        move_data = json.loads(last_move.move_data) if last_move.move_data else {}
        move_type = move_data.get("type", "unknown").upper()
        
        # Handle different move types according to contract
        if move_type == "PLACE":
            # For PLACE moves, try to get the word formed
            words_formed = move_data.get("words", [])
            if not words_formed:
                # Check for singular "word" field (computer moves)
                single_word = move_data.get("word", "")
                if single_word:
                    words_formed = [single_word]
            
            # Take the first/primary word for display
            word = words_formed[0] if words_formed else None
            points_earned = move_data.get("points", 0)
            
            # Handle different point field names (some moves use "score")
            if points_earned == 0:
                points_earned = move_data.get("score", 0)
                
        elif move_type in ["PASS", "EXCHANGE"]:
            # For PASS and EXCHANGE moves
            word = None
            points_earned = 0
        else:
            # Unknown move type - treat as PLACE
            word = None
            points_earned = move_data.get("points", move_data.get("score", 0))
        
        return {
            "player_username": last_move_player.username,
            "move_type": move_type,
            "word": word,
            "points_earned": points_earned,
            "timestamp": last_move.timestamp.isoformat()
        }
        
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        logger.error(f"Error parsing last move data for game {game_id}: {e}")
        # Return basic info even if move data is corrupted
        return {
            "player_username": last_move_player.username,
            "move_type": "UNKNOWN",
            "word": None,
            "points_earned": 0,
            "timestamp": last_move.timestamp.isoformat()
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
    
    # Get recent moves for highlighting (contract requirement)
    recent_moves = get_recent_moves_data(game.id, current_user_id, db)
    
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
        "user_score": next((p["score"] for p in players_info if p["is_current_user"]), 0),
        "recent_moves": recent_moves
    }

def get_recent_moves_data(game_id: str, current_user_id: int, db: Session) -> List[Dict[str, Any]]:
    """
    Get recent moves for last move highlighting feature.
    Returns moves from all players EXCEPT the current user, ordered by most recent first.
    
    For multi-player support:
    - 2 players: Returns 1 recent move (opponent's last move)
    - 3 players: Returns 2 recent moves (other players' last moves)
    - 4 players: Returns 3 recent moves (other players' last moves)
    
    Fully implements contract specification for recent_moves field.
    
    Args:
        game_id: Game ID
        current_user_id: Current user ID (to exclude their moves)
        db: Database session
        
    Returns:
        List of recent move data matching contract specification
    """
    # Get recent moves from all players except current user
    # Only include PLACE moves (not EXCHANGE or PASS) for highlighting
    recent_moves = db.query(Move)\
        .filter(Move.game_id == game_id)\
        .filter(Move.player_id != current_user_id)\
        .order_by(Move.timestamp.desc())\
        .limit(15)  # Get more than needed, then filter to get last move per player
    
    moves_data = []
    seen_players = set()  # Track players we've seen to get only last move per player
    
    for move in recent_moves:
        # Skip if we already have this player's most recent move
        if move.player_id in seen_players:
            continue
            
        try:
            move_data = json.loads(move.move_data) if move.move_data else {}
            move_type = move_data.get("type", "unknown")
            
            # Only include PLACE moves for highlighting (contract requirement)
            if move_type != "PLACE":
                seen_players.add(move.player_id)  # Mark as seen but don't include
                continue
            
            # Get player info
            player = db.query(User).filter(User.id == move.player_id).first()
            if not player:
                continue
                
            # Extract move positions from move data with enhanced tile information
            positions = []
            move_positions = move_data.get("data", [])
            
            for pos_data in move_positions:
                if isinstance(pos_data, dict):
                    # Calculate tile points based on letter and blank status
                    letter = pos_data.get("letter", "")
                    is_blank = pos_data.get("is_blank", False)
                    
                    # Basic point values for tiles (enhanced from simple default)
                    tile_points = 1  # Default for blanks
                    if not is_blank and letter:
                        # Standard Scrabble point values
                        point_values = {
                            'A': 1, 'E': 1, 'I': 1, 'O': 1, 'U': 1, 'L': 1, 'N': 1, 'S': 1, 'T': 1, 'R': 1,
                            'D': 2, 'G': 2,
                            'B': 3, 'C': 3, 'M': 3, 'P': 3,
                            'F': 4, 'H': 4, 'V': 4, 'W': 4, 'Y': 4,
                            'K': 5,
                            'J': 8, 'X': 8,
                            'Q': 10, 'Z': 10
                        }
                        tile_points = point_values.get(letter.upper(), 1)
                    
                    position = {
                        "row": pos_data.get("row", 0),
                        "col": pos_data.get("col", 0),
                        "letter": letter.upper(),
                        "points": tile_points,
                        "is_blank": is_blank
                    }
                    positions.append(position)
            
            # Only include moves that actually placed tiles
            if positions:
                # Extract additional move information for full contract compliance
                turn_number = move_data.get("turn_number", 0)
                points_earned = move_data.get("points", 0)
                
                # Handle different point field names (some moves use "score")
                if points_earned == 0:
                    points_earned = move_data.get("score", 0)
                
                # Handle both "words" (human moves) and "word" (computer moves) fields
                words_formed = move_data.get("words", [])
                if not words_formed:
                    # Check for singular "word" field (computer moves)
                    single_word = move_data.get("word", "")
                    if single_word:
                        words_formed = [single_word]
                
                # Ensure words_formed is a list of strings
                if isinstance(words_formed, str):
                    words_formed = [words_formed]
                elif not isinstance(words_formed, list):
                    words_formed = []
                
                # Calculate time ago for user-friendly display
                time_ago = datetime.now(timezone.utc) - move.timestamp
                
                # Format time ago in a human-readable way
                if time_ago.days > 0:
                    time_ago_str = f"{time_ago.days} day{'s' if time_ago.days != 1 else ''} ago"
                elif time_ago.seconds > 3600:
                    hours = time_ago.seconds // 3600
                    time_ago_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
                elif time_ago.seconds > 60:
                    minutes = time_ago.seconds // 60
                    time_ago_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                else:
                    time_ago_str = "Just now"
                
                # Enhanced move info with comprehensive details for frontend
                move_info = {
                    # Player information (WHO)
                    "player_id": str(move.player_id),
                    "player_username": player.username,
                    "is_computer": is_computer_user_id(move.player_id, db),
                    
                    # Timing information (WHEN)
                    "timestamp": move.timestamp.isoformat(),
                    "timestamp_unix": int(move.timestamp.timestamp()),
                    "time_ago": time_ago_str,
                    "turn_number": turn_number,
                    
                    # Move details (WHAT)
                    "move_type": move_type,
                    "words_formed": words_formed,
                    "points_earned": points_earned,
                    "positions": positions,
                    
                    # Additional context for frontend
                    "move_summary": _generate_move_summary(words_formed, points_earned, move_type),
                    "tile_count": len(positions)
                }
                moves_data.append(move_info)
                seen_players.add(move.player_id)
                
        except Exception as e:
            logger.error(f"Error processing move {move.id} for recent moves: {e}")
            continue
    
    # Sort by timestamp (most recent first) and limit based on game size
    # Contract specifies: max_players - 1 moves (up to 3 moves for 4-player games)
    moves_data.sort(key=lambda x: x["timestamp"], reverse=True)
    return moves_data[:3]  # Maximum 3 recent moves for 4-player games

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
    
    # Get recent moves for highlighting
    recent_moves = get_recent_moves_data(game.id, current_user_id, db)
    
    # Get last move summary for frontend contract compliance
    last_move_summary = get_last_move_summary(game.id, db)
    
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
        "consecutive_passes": state_data.get("consecutive_passes", 0),
        "recent_moves": recent_moves,
        "last_move": last_move_summary
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

def _generate_move_summary(words_formed: List[str], points_earned: int, move_type: str) -> str:
    """
    Generate a human-readable summary of a move for frontend display.
    
    Args:
        words_formed: List of words formed in the move
        points_earned: Points earned from the move
        move_type: Type of move (PLACE, PASS, EXCHANGE)
        
    Returns:
        Human-readable move summary
    """
    if move_type == "PLACE" and words_formed:
        if len(words_formed) == 1:
            return f"Played '{words_formed[0]}' for {points_earned} points"
        else:
            words_str = "', '".join(words_formed)
            return f"Played '{words_str}' for {points_earned} points"
    elif move_type == "PLACE":
        return f"Placed tiles for {points_earned} points"
    elif move_type == "PASS":
        return "Passed turn"
    elif move_type == "EXCHANGE":
        return "Exchanged letters"
    else:
        return f"Made a {move_type.lower()} move"