"""
Simple Computer Player - Fast and Reliable
No complex filtering, no expensive operations, just works.
"""

import random
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class SimpleComputerPlayer:
    """Simple computer player that makes basic but valid moves quickly."""
    
    def __init__(self, rack: List[str], difficulty: str = "medium"):
        self.rack = rack
        self.difficulty = difficulty
        
    def make_move(self, board: List[List], language: str = "de") -> Optional[Dict[str, Any]]:
        """Make a simple move - find any valid word placement."""
        logger.info(f"🤖 Simple AI: Making move with rack {self.rack}")
        
        # Simple word list - common German words that are likely to work
        simple_words = [
            "ICH", "DU", "ER", "SIE", "WIR", "IHR", "DAS", "DIE", "DER", "UND",
            "IST", "BIN", "HAT", "MIT", "AUS", "ZU", "VON", "FÜR", "AUF", "AN",
            "UM", "SO", "WAS", "WER", "WIE", "WO", "DA", "JA", "NEIN", "GUT",
            "NEU", "ALT", "GROß", "KLEIN", "LANG", "KURZ", "HOCH", "TIEF",
            "HAUS", "AUTO", "BUCH", "HAND", "KOPF", "AUGE", "OHR", "MUND",
            "TAG", "NACHT", "JAHR", "ZEIT", "WELT", "LAND", "STADT", "DORF",
            "MANN", "FRAU", "KIND", "BABY", "HUND", "KATZE", "BAUM", "BLUME"
        ]
        
        # Try to make words from our rack
        possible_words = []
        rack_letters = [letter.upper() for letter in self.rack]
        
        for word in simple_words:
            if self._can_make_word(word, rack_letters):
                possible_words.append(word)
        
        logger.info(f"🤖 Simple AI: Found {len(possible_words)} possible words: {possible_words[:5]}...")
        
        if not possible_words:
            logger.info("🤖 Simple AI: No words possible, passing")
            return None
            
        # Try each word on the board
        for word in possible_words[:10]:  # Only try first 10 words
            move = self._try_place_word(board, word, rack_letters)
            if move:
                logger.info(f"🤖 Simple AI: Successfully placed '{word}' for {move.get('score', 0)} points")
                return move
                
        logger.info("🤖 Simple AI: Could not place any words, passing")
        return None
    
    def _can_make_word(self, word: str, rack_letters: List[str]) -> bool:
        """Check if we can make this word with our rack letters."""
        rack_copy = rack_letters.copy()
        
        for letter in word:
            if letter in rack_copy:
                rack_copy.remove(letter)
            else:
                return False
        return True
    
    def _try_place_word(self, board: List[List], word: str, rack_letters: List[str]) -> Optional[Dict[str, Any]]:
        """Try to place a word on the board - very simple placement logic."""
        
        # Check if board is empty (first move)
        board_empty = all(all(cell is None for cell in row) for row in board)
        
        if board_empty:
            # First move: place horizontally through center
            return self._place_first_move(word, rack_letters)
        else:
            # Subsequent moves: try to connect to existing tiles
            return self._place_connecting_move(board, word, rack_letters)
    
    def _place_first_move(self, word: str, rack_letters: List[str]) -> Dict[str, Any]:
        """Place the first move through the center star."""
        center_row, center_col = 7, 7
        start_col = center_col - len(word) // 2
        
        tiles = []
        for i, letter in enumerate(word):
            tiles.append({
                "row": center_row,
                "col": start_col + i,
                "letter": letter,
                "is_blank": False
            })
        
        # Simple scoring - just count letters
        score = len(word) * 2  # Basic scoring
        
        return {
            "word": word,
            "tiles": tiles,
            "score": score,
            "start_pos": {"row": center_row, "col": start_col},
            "direction": "horizontal"
        }
    
    def _place_connecting_move(self, board: List[List], word: str, rack_letters: List[str]) -> Optional[Dict[str, Any]]:
        """Try to place word connecting to existing tiles."""
        
        # Find existing tiles
        existing_positions = []
        for row in range(15):
            for col in range(15):
                if board[row][col] is not None:
                    existing_positions.append((row, col))
        
        if not existing_positions:
            return None
            
        # Try to place word adjacent to existing tiles (simplified)
        for row, col in existing_positions[:5]:  # Only try first 5 positions
            
            # Try horizontal placement to the right
            if col + len(word) < 15:
                if self._is_valid_placement(board, word, row, col + 1, "horizontal"):
                    return self._create_move(word, row, col + 1, "horizontal", rack_letters)
            
            # Try vertical placement downward  
            if row + len(word) < 15:
                if self._is_valid_placement(board, word, row + 1, col, "vertical"):
                    return self._create_move(word, row + 1, col, "vertical", rack_letters)
        
        return None
    
    def _is_valid_placement(self, board: List[List], word: str, start_row: int, start_col: int, direction: str) -> bool:
        """Simple validation - just check if positions are empty."""
        for i in range(len(word)):
            if direction == "horizontal":
                row, col = start_row, start_col + i
            else:
                row, col = start_row + i, start_col
                
            if row >= 15 or col >= 15 or board[row][col] is not None:
                return False
        return True
    
    def _create_move(self, word: str, start_row: int, start_col: int, direction: str, rack_letters: List[str]) -> Dict[str, Any]:
        """Create a move dictionary."""
        tiles = []
        for i, letter in enumerate(word):
            if direction == "horizontal":
                row, col = start_row, start_col + i
            else:
                row, col = start_row + i, start_col
                
            tiles.append({
                "row": row,
                "col": col,
                "letter": letter,
                "is_blank": False
            })
        
        return {
            "word": word,
            "tiles": tiles,
            "score": len(word) * 2,  # Simple scoring
            "start_pos": {"row": start_row, "col": start_col},
            "direction": direction
        } 