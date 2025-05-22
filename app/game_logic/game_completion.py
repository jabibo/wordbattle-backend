from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.models import Game, Player, Move
from app.config import GAME_INACTIVE_DAYS
import json
from datetime import datetime, timezone, timedelta

def check_game_completion(game_id: str, db: Session) -> Tuple[bool, Optional[Dict]]:
    """
    Check if a game is complete based on various conditions.
    
    Conditions for game completion:
    1. Three consecutive passes by all players
    2. No more letters in the bag and one player has used all their letters
    3. Game has been inactive for more than the configured number of days
    
    Returns:
        Tuple of (is_complete, completion_data)
        where completion_data contains details about the completion
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        return False, None
    
    players = db.query(Player).filter(Player.game_id == game_id).all()
    if not players:
        return False, None
    
    # Check for empty rack (player has used all letters)
    for player in players:
        if player.rack == "":
            return True, {
                "reason": "player_empty_rack",
                "winner_id": player.user_id,
                "scores": {p.user_id: p.score for p in players}
            }
    
    # Check for consecutive passes
    moves = db.query(Move).filter(Move.game_id == game_id).order_by(Move.timestamp.desc()).limit(len(players) * 3).all()
    if len(moves) >= len(players) * 3:
        # Check if the last N*3 moves are all passes
        pass_count = 0
        for move in moves:
            move_data = json.loads(move.move_data)
            if not move_data:  # Empty move data indicates a pass
                pass_count += 1
            else:
                break
        
        if pass_count >= len(players) * 3:
            # All players have passed three times in a row
            return True, {
                "reason": "consecutive_passes",
                "scores": {p.user_id: p.score for p in players},
                "winner_id": max(players, key=lambda p: p.score).user_id
            }
    
    # Check for inactivity
    last_move = db.query(Move).filter(Move.game_id == game_id).order_by(Move.timestamp.desc()).first()
    if last_move and (datetime.now(timezone.utc) - last_move.timestamp) > timedelta(days=GAME_INACTIVE_DAYS):
        return True, {
            "reason": "inactivity",
            "scores": {p.user_id: p.score for p in players},
            "winner_id": max(players, key=lambda p: p.score).user_id
        }
    
    return False, None

def finalize_game(game_id: str, db: Session) -> Dict:
    """
    Finalize a completed game.
    
    This will:
    1. Mark the game as completed
    2. Calculate final scores
    3. Determine the winner
    
    Returns:
        Dict with game completion details
    """
    is_complete, completion_data = check_game_completion(game_id, db)
    
    if not is_complete:
        # Check if any player has an empty rack as a final check
        players = db.query(Player).filter(Player.game_id == game_id).all()
        for player in players:
            if player.rack == "":
                completion_data = {
                    "reason": "player_empty_rack",
                    "winner_id": player.user_id,
                    "scores": {p.user_id: p.score for p in players}
                }
                break
        
        if not completion_data:
            # Force game completion with current state
            completion_data = {
                "reason": "manual_completion",
                "scores": {p.user_id: p.score for p in players},
                "winner_id": max(players, key=lambda p: p.score).user_id if players else None
            }
    
    # Update game state to mark as completed
    game = db.query(Game).filter(Game.id == game_id).first()
    if game:
        # Store completion data in the game state
        board = json.loads(game.state)
        game_state = {
            "board": board,
            "completed": True,
            "completion_data": completion_data,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        game.state = json.dumps(game_state)
        game.current_player_id = None  # No current player in completed game
        db.commit()
    
    return completion_data