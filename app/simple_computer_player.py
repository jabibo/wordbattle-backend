"""
Simple Computer Player - Fast and Reliable with Proper Validation
Uses simple word list but validates moves properly.
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
        
    def make_move(self, board: List[List], language: str = "de", wordlist: Optional[set] = None) -> Optional[Dict[str, Any]]:
        """Make a simple move - find any valid word placement."""
        logger.info(f"🤖 Simple AI: Making move with rack {self.rack}")
        
        # Load wordlist if not provided (for validation)
        if wordlist is None:
            from app.utils.wordlist_utils import load_wordlist
            wordlist = load_wordlist(language)
            if not wordlist:
                logger.error(f"🤖 Simple AI: No wordlist available for {language}")
                return None
        
        # IMPROVED: Smart word selection from full wordlist instead of hardcoded list
        # Get rack letters for filtering
        rack_letters_set = set(letter.upper() for letter in self.rack)
        
        # Intelligently filter wordlist to manageable size while maintaining good coverage
        candidate_words = []
        for word in wordlist:
            word_upper = word.upper()
            # Filter to reasonable words that could potentially be played
            if (2 <= len(word_upper) <= 7 and  # Scrabble word length range
                len(set(word_upper) & rack_letters_set) >= 1):  # Share at least one letter with rack
                candidate_words.append(word_upper)
                # Limit to prevent performance issues while ensuring good coverage
                if len(candidate_words) >= 1000:  # 1000 candidates should be plenty
                    break
        
        logger.info(f"🤖 Simple AI: Found {len(candidate_words)} candidate words from full dictionary")
        
        # For safety, also include some common short words for any language
        common_short_words = ["A", "I", "IS", "IT", "TO", "OF", "IN", "ON", "AT", "BE", "OR", "AS", "AN", "GO", "NO", "SO", "UP", "WE", "ME", "MY"]
        for word in common_short_words:
            if word.upper() in wordlist and word.upper() not in candidate_words:
                candidate_words.append(word.upper())
        
        valid_simple_words = candidate_words
        logger.info(f"🤖 Simple AI: Using {len(valid_simple_words)} words for move generation")
        
        # Try to make words from our rack
        possible_words = []
        rack_letters = [letter.upper() for letter in self.rack]
        
        for word in valid_simple_words:
            if self._can_make_word(word, rack_letters):
                possible_words.append(word)
        
        logger.info(f"🤖 Simple AI: Found {len(possible_words)} possible words: {possible_words[:5]}...")
        
        if not possible_words:
            logger.info("🤖 Simple AI: No words possible, passing")
            return None
            
        # Try each word on the board with ENHANCED validation
        for word in possible_words[:10]:  # Only try first 10 words
            logger.info(f"🤖 Simple AI: Attempting to place word '{word}'")
            move = self._try_place_word_with_enhanced_validation(board, word, rack_letters, wordlist)
            if move:
                logger.info(f"🤖 Simple AI: Successfully placed '{word}' for {move.get('score', 0)} points")
                return move
            else:
                logger.info(f"🤖 Simple AI: Could not place '{word}' - validation failed")
                
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
    
    def _try_place_word_with_enhanced_validation(self, board: List[List], word: str, rack_letters: List[str], wordlist: set) -> Optional[Dict[str, Any]]:
        """Try to place a word on the board with enhanced validation."""
        
        # FIRST: Validate that the main word is in the dictionary
        if not self._is_word_in_dictionary(word, wordlist):
            logger.warning(f"🤖 Simple AI: Main word '{word}' not in dictionary!")
            return None
        
        # Check if board is empty (first move)
        board_empty = all(all(cell is None for cell in row) for row in board)
        
        if board_empty:
            # First move: place horizontally through center
            return self._place_first_move_validated(word, rack_letters)
        else:
            # Subsequent moves: try to connect to existing tiles with enhanced validation
            return self._place_connecting_move_enhanced_validation(board, word, rack_letters, wordlist)
    
    def _is_word_in_dictionary(self, word: str, wordlist: set) -> bool:
        """Check if a word is in the dictionary with multiple case variations."""
        return (word.upper() in wordlist or 
                word.lower() in wordlist or 
                word.capitalize() in wordlist or 
                word in wordlist)
    
    def _place_first_move_validated(self, word: str, rack_letters: List[str]) -> Dict[str, Any]:
        """Place the first move through the center star."""
        center_row, center_col = 7, 7
        start_col = center_col - len(word) // 2
        
        # Ensure word fits on board
        if start_col < 0 or start_col + len(word) > 15:
            return None
        
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
    
    def _place_connecting_move_enhanced_validation(self, board: List[List], word: str, rack_letters: List[str], wordlist: set) -> Optional[Dict[str, Any]]:
        """Try to place word connecting to existing tiles with enhanced validation."""
        
        # Find existing tiles
        existing_positions = []
        for row in range(15):
            for col in range(15):
                if board[row][col] is not None:
                    existing_positions.append((row, col))
        
        if not existing_positions:
            return None
            
        # Try to place word adjacent to existing tiles
        for row, col in existing_positions[:5]:  # Only try first 5 positions
            
            # Try horizontal placement to the right
            if col + len(word) < 15:
                move = self._try_placement_with_enhanced_validation(board, word, row, col + 1, "horizontal", rack_letters, wordlist)
                if move:
                    return move
            
            # Try vertical placement downward  
            if row + len(word) < 15:
                move = self._try_placement_with_enhanced_validation(board, word, row + 1, col, "vertical", rack_letters, wordlist)
                if move:
                    return move
                    
            # Try horizontal placement to the left
            if col - len(word) >= 0:
                move = self._try_placement_with_enhanced_validation(board, word, row, col - len(word), "horizontal", rack_letters, wordlist)
                if move:
                    return move
            
            # Try vertical placement upward
            if row - len(word) >= 0:
                move = self._try_placement_with_enhanced_validation(board, word, row - len(word), col, "vertical", rack_letters, wordlist)
                if move:
                    return move
        
        return None
    
    def _try_placement_with_enhanced_validation(self, board: List[List], word: str, start_row: int, start_col: int, direction: str, rack_letters: List[str], wordlist: set) -> Optional[Dict[str, Any]]:
        """Try placing word at specific position with enhanced validation."""
        
        # Check basic bounds and connectivity
        if not self._is_valid_placement_basic(board, word, start_row, start_col, direction):
            return None
            
        # Check if placement connects to existing tiles
        if not self._placement_connects_to_board(board, word, start_row, start_col, direction):
            return None
            
        # ENHANCED: Check ALL cross-words formed with strict validation
        if not self._check_all_cross_words_strict(board, word, start_row, start_col, direction, wordlist):
            return None
            
        return self._create_move(word, start_row, start_col, direction, rack_letters)
    
    def _is_valid_placement_basic(self, board: List[List], word: str, start_row: int, start_col: int, direction: str) -> bool:
        """Basic validation - check bounds and empty spaces."""
        for i in range(len(word)):
            if direction == "horizontal":
                row, col = start_row, start_col + i
            else:
                row, col = start_row + i, start_col
                
            if row >= 15 or col >= 15 or row < 0 or col < 0:
                return False
            if board[row][col] is not None:
                return False
        return True
    
    def _placement_connects_to_board(self, board: List[List], word: str, start_row: int, start_col: int, direction: str) -> bool:
        """Check if placement connects to at least one existing tile."""
        for i in range(len(word)):
            if direction == "horizontal":
                row, col = start_row, start_col + i
            else:
                row, col = start_row + i, start_col
                
            # Check adjacent positions for existing tiles
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                adj_row, adj_col = row + dr, col + dc
                if 0 <= adj_row < 15 and 0 <= adj_col < 15:
                    if board[adj_row][adj_col] is not None:
                        return True
        return False
    
    def _check_all_cross_words_strict(self, board: List[List], word: str, start_row: int, start_col: int, direction: str, wordlist: set) -> bool:
        """Strict cross-word validation - check if all cross-words formed are valid."""
        for i in range(len(word)):
            if direction == "horizontal":
                row, col = start_row, start_col + i
                # Check vertical cross-word
                cross_word = self._get_cross_word_at_position(board, row, col, "vertical", word[i])
            else:
                row, col = start_row + i, start_col
                # Check horizontal cross-word
                cross_word = self._get_cross_word_at_position(board, row, col, "horizontal", word[i])
                
            if cross_word and len(cross_word) > 1:
                # STRICT validation: cross-word must be in dictionary
                if not self._is_word_in_dictionary(cross_word, wordlist):
                    logger.warning(f"🤖 Simple AI: Invalid cross-word '{cross_word}' would be formed at ({row},{col})")
                    return False
                else:
                    logger.info(f"🤖 Simple AI: Valid cross-word '{cross_word}' formed at ({row},{col})")
        
        logger.info(f"🤖 Simple AI: All cross-words validated successfully")
        return True
    
    def _get_cross_word_at_position(self, board: List[List], row: int, col: int, direction: str, new_letter: str) -> str:
        """Get the cross-word that would be formed at a position."""
        word_letters = []
        
        if direction == "vertical":
            # Look up
            r = row - 1
            while r >= 0 and board[r][col] is not None:
                word_letters.insert(0, board[r][col]["letter"])
                r -= 1
            
            # Add new letter
            word_letters.append(new_letter)
            
            # Look down
            r = row + 1
            while r < 15 and board[r][col] is not None:
                word_letters.append(board[r][col]["letter"])
                r += 1
        else:  # horizontal
            # Look left
            c = col - 1
            while c >= 0 and board[row][c] is not None:
                word_letters.insert(0, board[row][c]["letter"])
                c -= 1
            
            # Add new letter
            word_letters.append(new_letter)
            
            # Look right
            c = col + 1
            while c < 15 and board[row][c] is not None:
                word_letters.append(board[row][c]["letter"])
                c += 1
        
        return "".join(word_letters) if len(word_letters) > 1 else ""
    
    def _create_move(self, word: str, start_row: int, start_col: int, direction: str, rack_letters: List[str]) -> Dict[str, Any]:
        """Create a move dictionary."""
        logger.info(f"🤖 Simple AI: Creating move for word '{word}' at ({start_row},{start_col}) {direction}")
        
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
        
        move_result = {
            "word": word,
            "tiles": tiles,
            "score": len(word) * 2,  # Simple scoring
            "start_pos": {"row": start_row, "col": start_col},
            "direction": direction
        }
        
        logger.info(f"🤖 Simple AI: Move created successfully - word: '{word}', tiles: {len(tiles)}, score: {move_result['score']}")
        return move_result 