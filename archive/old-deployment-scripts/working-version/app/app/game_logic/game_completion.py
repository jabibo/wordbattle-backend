from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.models import Game, Player, Move
from app.config import GAME_INACTIVE_DAYS
import json
from datetime import datetime, timezone, timedelta
from app.models.game import GameStatus
from app.game_logic.game_state import GameState, GamePhase
from app.routers.games import GameStateEncoder

def check_game_completion(game: Game, game_state: GameState) -> bool:
    """Check if the game should be completed and update its status if so."""
    is_complete, completion_data = game_state.check_game_end()
    
    if is_complete:
        # Update game status
        game.status = GameStatus.COMPLETED
        
        # Update game state
        state_data = json.loads(game.state)
        state_data["phase"] = GamePhase.COMPLETED.value
        state_data["completion_data"] = completion_data
        game.state = json.dumps(state_data, cls=GameStateEncoder)
        
        return True
    
    return False

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