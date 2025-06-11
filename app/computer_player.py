"""
Computer Player System for WordBattle

This module provides a computer player that can play against human users
without being stored as a real user in the database.
"""

import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.game_logic.game_state import GameState, GamePhase, MoveType, Position, PlacedTile
from app.game_logic.board_utils import find_word_placements, is_valid_word_placement
from app.game_logic.letter_bag import draw_letters
from app.utils.wordlist_utils import load_wordlist
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ComputerPlayer:
    """A computer player that can make moves in WordBattle games."""
    
    def __init__(self, difficulty: str = "medium"):
        self.difficulty = difficulty  # easy, medium, hard
        self.player_id = -1  # Special ID for computer player
        self.username = "Computer"
        self.display_name = "Computer Player"
        
    def get_virtual_user_data(self) -> Dict[str, Any]:
        """Get virtual user data for the computer player."""
        return {
            "id": self.player_id,
            "username": self.username,
            "email": "computer@wordbattle.ai",
            "display_name": self.display_name,
            "is_computer": True
        }
    
    def make_move(self, game_state_data: Dict[str, Any], rack: str, wordlist: List[str], db: Session) -> Dict[str, Any]:
        """
        Make a move for the computer player.
        
        Args:
            game_state_data: Current game state
            rack: Computer player's current letter rack
            wordlist: Available words for the language
            db: Database session
            
        Returns:
            Move data dictionary or None if passing
        """
        try:
            # Parse game state
            board = game_state_data.get("board", [[None for _ in range(15)] for _ in range(15)])
            language = game_state_data.get("language", "en")
            
            # Convert rack string to list
            rack_letters = list(rack)
            
            # Find possible word placements
            possible_moves = self._find_possible_moves(board, rack_letters, wordlist)
            
            if not possible_moves:
                logger.info(f"Computer player: No moves found, passing turn")
                return {
                    "type": "pass",
                    "message": "Computer player passes"
                }
            
            # Select best move based on difficulty
            selected_move = self._select_move_by_difficulty(possible_moves)
            
            logger.info(f"Computer player making move: {selected_move['word']} for {selected_move['score']} points")
            
            return {
                "type": "place_tiles",
                "tiles": selected_move["tiles"],
                "word": selected_move["word"],
                "score": selected_move["score"],
                "message": f"Computer played '{selected_move['word']}' for {selected_move['score']} points"
            }
            
        except Exception as e:
            logger.error(f"Computer player move generation failed: {e}")
            return {
                "type": "pass",
                "message": "Computer player passes due to error"
            }
    
    def _find_possible_moves(self, board: List[List], rack_letters: List[str], wordlist: List[str]) -> List[Dict[str, Any]]:
        """Find all possible moves for the current board state and rack."""
        possible_moves = []
        
        # Sample a subset of wordlist for performance (based on difficulty)
        if self.difficulty == "easy":
            sample_size = min(1000, len(wordlist))
        elif self.difficulty == "medium":
            sample_size = min(3000, len(wordlist))
        else:  # hard
            sample_size = min(5000, len(wordlist))
        
        sampled_words = random.sample(wordlist, sample_size) if len(wordlist) > sample_size else wordlist
        
        # Try each word from the wordlist
        for word in sampled_words:
            if len(word) < 2 or len(word) > 7:  # Reasonable word length limits
                continue
                
            # Check if we can make this word with our rack
            if not self._can_make_word(word.upper(), rack_letters):
                continue
            
            # Try to place the word on the board
            placements = self._find_word_placements_on_board(board, word.upper(), rack_letters)
            
            for placement in placements:
                possible_moves.append({
                    "word": word.upper(),
                    "tiles": placement["tiles"],
                    "score": placement["score"],
                    "start_pos": placement["start_pos"],
                    "direction": placement["direction"]
                })
        
        # Sort by score (best moves first)
        possible_moves.sort(key=lambda x: x["score"], reverse=True)
        
        return possible_moves[:50]  # Limit to top 50 moves for performance
    
    def _can_make_word(self, word: str, rack_letters: List[str]) -> bool:
        """Check if a word can be made with the available rack letters."""
        rack_copy = rack_letters.copy()
        
        for letter in word:
            if letter in rack_copy:
                rack_copy.remove(letter)
            elif '*' in rack_copy:  # Blank tile
                rack_copy.remove('*')
            else:
                return False
        
        return True
    
    def _find_word_placements_on_board(self, board: List[List], word: str, rack_letters: List[str]) -> List[Dict[str, Any]]:
        """Find valid placements for a word on the board."""
        placements = []
        
        # Try horizontal placements
        for row in range(15):
            for col in range(15 - len(word) + 1):
                placement = self._try_placement(board, word, row, col, "horizontal", rack_letters)
                if placement:
                    placements.append(placement)
        
        # Try vertical placements
        for row in range(15 - len(word) + 1):
            for col in range(15):
                placement = self._try_placement(board, word, row, col, "vertical", rack_letters)
                if placement:
                    placements.append(placement)
        
        return placements
    
    def _try_placement(self, board: List[List], word: str, start_row: int, start_col: int, 
                      direction: str, rack_letters: List[str]) -> Optional[Dict[str, Any]]:
        """Try to place a word at a specific position and direction."""
        tiles = []
        rack_copy = rack_letters.copy()
        score = 0
        touches_existing = False
        
        # Check if placement is valid
        for i, letter in enumerate(word):
            if direction == "horizontal":
                row, col = start_row, start_col + i
            else:  # vertical
                row, col = start_row + i, start_col
            
            if row >= 15 or col >= 15:
                return None
            
            existing_tile = board[row][col]
            
            if existing_tile is not None:
                # Letter already on board - must match
                if existing_tile != letter:
                    return None
                touches_existing = True
            else:
                # Need to place a tile from rack
                if letter in rack_copy:
                    rack_copy.remove(letter)
                elif '*' in rack_copy:  # Blank tile
                    rack_copy.remove('*')
                else:
                    return None
                
                tiles.append({
                    "row": row,
                    "col": col,
                    "letter": letter
                })
        
        # Must touch at least one existing tile (except for first move)
        if not touches_existing and any(any(row) for row in board):
            return None
        
        # First move must go through center (7,7)
        if not any(any(row) for row in board):
            center_covered = False
            for i in range(len(word)):
                if direction == "horizontal":
                    if start_row == 7 and start_col + i == 7:
                        center_covered = True
                else:
                    if start_row + i == 7 and start_col == 7:
                        center_covered = True
            if not center_covered:
                return None
        
        # Calculate basic score (simplified scoring)
        score = len(word) * 10  # Basic scoring
        if len(word) >= 5:
            score += 20  # Bonus for longer words
        
        return {
            "tiles": tiles,
            "score": score,
            "start_pos": (start_row, start_col),
            "direction": direction
        }
    
    def _select_move_by_difficulty(self, possible_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select a move based on the computer player's difficulty level."""
        if not possible_moves:
            return None
        
        if self.difficulty == "easy":
            # Easy: Random move from bottom 50% of moves
            bottom_half = possible_moves[len(possible_moves)//2:]
            return random.choice(bottom_half) if bottom_half else possible_moves[-1]
        
        elif self.difficulty == "medium":
            # Medium: Random move from top 50% of moves
            top_half = possible_moves[:len(possible_moves)//2 + 1]
            return random.choice(top_half)
        
        else:  # hard
            # Hard: Best move with small random variation
            top_moves = possible_moves[:min(3, len(possible_moves))]
            return random.choice(top_moves)


def create_computer_player(difficulty: str = "medium") -> ComputerPlayer:
    """Create a new computer player instance."""
    return ComputerPlayer(difficulty)


def add_computer_player_to_game(game_id: str, db: Session, difficulty: str = "medium") -> Dict[str, Any]:
    """
    Add a computer player to an existing game.
    
    Args:
        game_id: ID of the game to join
        db: Database session
        difficulty: Computer player difficulty level
        
    Returns:
        Dictionary with computer player information
    """
    from app.models import Game, Player
    
    # Get the game
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise ValueError("Game not found")
    
    # Check if game is in setup phase
    if game.status.value != "setup":
        raise ValueError("Can only add computer player during game setup")
    
    # Check if there's room for another player
    current_players = db.query(Player).filter(Player.game_id == game_id).count()
    if current_players >= game.max_players:
        raise ValueError("Game is already full")
    
    # Create computer player
    computer_player = Player(
        game_id=game_id,
        user_id=-1,  # Special ID for computer player
        score=0,
        rack=""  # Will be dealt when game starts
    )
    
    db.add(computer_player)
    db.commit()
    db.refresh(computer_player)
    
    logger.info(f"Computer player added to game {game_id} with difficulty {difficulty}")
    
    return {
        "player_id": computer_player.id,
        "user_id": -1,
        "username": "Computer",
        "display_name": "Computer Player",
        "difficulty": difficulty,
        "is_computer": True
    } 