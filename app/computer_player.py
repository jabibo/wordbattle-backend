"""
Computer Player System for WordBattle

This module provides a computer player that can play against human users
without being stored as a real user in the database.
"""

import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.game_logic.game_state import GameState, GamePhase, MoveType, Position, PlacedTile
from app.game_logic.board_utils import find_word_placements
from app.game_logic.letter_bag import draw_letters, LETTER_DISTRIBUTION
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
            # Enhanced debugging - log critical information
            logger.info(f"🤖 COMPUTER PLAYER DEBUG START 🤖")
            logger.info(f"🤖 Rack: '{rack}' (length: {len(rack)})")
            logger.info(f"🤖 Wordlist size: {len(wordlist) if wordlist else 'None/Empty'}")
            logger.info(f"🤖 Game state keys: {list(game_state_data.keys()) if game_state_data else 'None'}")
            
            # Parse game state
            board = game_state_data.get("board", [[None for _ in range(15)] for _ in range(15)])
            language = game_state_data.get("language", "en")
            
            # Convert rack string to list
            rack_letters = list(rack) if rack else []
            
            # Enhanced rack debugging
            if not rack_letters:
                logger.error(f"🤖 CRITICAL: Computer player has EMPTY RACK!")
                return {
                    "type": "pass",
                    "message": "Computer player passes - empty rack"
                }
            
            # Enhanced wordlist debugging
            if not wordlist:
                logger.error(f"🤖 CRITICAL: Computer player has NO WORDLIST!")
                return {
                    "type": "pass",
                    "message": "Computer player passes - no wordlist"
                }
            
            # Sample some words from wordlist for debugging
            sample_words = wordlist[:10] if len(wordlist) >= 10 else wordlist
            logger.info(f"🤖 Sample words from wordlist: {sample_words}")
            
            # Debug: Log board format
            tiles_on_board = 0
            for row in board:
                for cell in row:
                    if cell is not None:
                        tiles_on_board += 1
                        if tiles_on_board <= 3:  # Log first few tiles for debugging
                            logger.info(f"🤖 Board cell example: {cell} (type: {type(cell)})")
            
            # Check if board is empty (first move)
            board_is_empty = tiles_on_board == 0
            logger.info(f"🤖 Board has {tiles_on_board} tiles, Rack: {rack_letters}, Language: {language}")
            
            # Test if we can make some basic words
            test_words = ["KRAFT", "FAKT", "TRAF", "AUS", "IST", "DAS"]
            logger.info(f"🤖 Testing basic word formation:")
            for test_word in test_words:
                if test_word in wordlist:
                    can_make = self._can_make_word(test_word, rack_letters)
                    logger.info(f"🤖   '{test_word}': can_make={can_make}")
                    if can_make:
                        logger.info(f"🤖   ✅ Found makeable word: {test_word}")
                        break
                else:
                    logger.info(f"🤖   '{test_word}': not in wordlist")
            
            # Find possible word placements
            logger.info(f"🤖 Starting move search...")
            possible_moves = self._find_possible_moves(board, rack_letters, wordlist, language)
            
            logger.info(f"🤖 RESULT: Found {len(possible_moves)} possible moves")
            if possible_moves:
                logger.info(f"🤖 Top 3 moves: {possible_moves[:3]}")
            else:
                logger.error(f"🤖 CRITICAL: NO MOVES FOUND - Computer will pass!")
            
            if not possible_moves:
                logger.info(f"🤖 COMPUTER PLAYER DEBUG END - PASSING 🤖")
                return {
                    "type": "pass",
                    "message": "Computer player passes"
                }
            
            # Select best move based on difficulty
            selected_move = self._select_move_by_difficulty(possible_moves)
            
            logger.info(f"🤖 SELECTED MOVE: {selected_move['word']} for {selected_move['score']} points")
            logger.info(f"🤖 COMPUTER PLAYER DEBUG END - PLACING TILES 🤖")
            
            return {
                "type": "place_tiles",
                "tiles": selected_move["tiles"],
                "word": selected_move["word"],
                "score": selected_move["score"],
                "message": f"Computer played '{selected_move['word']}' for {selected_move['score']} points"
            }
            
        except Exception as e:
            logger.error(f"🤖 CRITICAL ERROR: Computer player move generation failed: {e}")
            logger.error(f"🤖 Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"🤖 Traceback: {traceback.format_exc()}")
            return {
                "type": "pass",
                "message": "Computer player passes due to error"
            }
    
    def _find_possible_moves(self, board: List[List], rack_letters: List[str], wordlist: List[str], language: str = "en") -> List[Dict[str, Any]]:
        """Find all possible moves for the current board state and rack."""
        possible_moves = []
        
        logger.info(f"🤖 Computer player: Starting move search with rack {rack_letters}")
        
        # ULTRA AGGRESSIVE PERFORMANCE OPTIMIZATION: Drastically reduce wordlist
        max_words_to_check = 500  # Reduce from 5000 to 500 words only!
        
        # Pre-filter by length and common letters to avoid expensive operations
        rack_set = set(rack_letters)
        quick_filtered = []
        
        # EFFICIENT FIX: Use a curated list of common valid words for better performance
        if language.lower() == "de":
            # Common German words that are likely to be valid
            common_words = [
                "ICH", "DU", "ER", "SIE", "WIR", "IHR", "DAS", "DIE", "DER", "UND", "IST", "BIN", "HAT", 
                "MIT", "AUS", "ZU", "VON", "FÜR", "AUF", "AN", "UM", "SO", "WAS", "WER", "WIE", "WO", 
                "DA", "JA", "NEIN", "GUT", "NEU", "ALT", "GROSS", "KLEIN", "LANG", "KURZ", "HOCH", "TIEF",
                "HAUS", "AUTO", "BUCH", "HAND", "KOPF", "AUGE", "OHR", "MUND", "TAG", "NACHT", "JAHR", 
                "ZEIT", "WELT", "LAND", "STADT", "DORF", "MANN", "FRAU", "KIND", "BABY", "HUND", "KATZE",
                "BAUM", "BLUME", "KRAFT", "FEST", "SPIEL", "ARBEIT", "LEBEN", "LIEBE", "FREUND", "SCHULE",
                "WASSER", "FEUER", "LUFT", "ERDE"
            ]
            
            # Filter common words by what we can make
            for word in common_words:
                word_upper = word.upper()
                word_letters = set(word_upper)
                if word_letters.issubset(rack_set | {'?', '*'}) and self._can_make_word(word_upper, rack_letters):
                    quick_filtered.append(word_upper)
        
        # If we didn't find enough common words, check some from the full wordlist
        if len(quick_filtered) < 5:
            check_limit = min(1000, len(wordlist))  # Reduced from 2000
            for i, word in enumerate(wordlist[:check_limit]):
                if i >= max_words_to_check or len(quick_filtered) >= 10:  # Stop early
                    break
                    
                # Quick length filter
                if not (2 <= len(word) <= 6):
                    continue
                    
                # Quick letter filter - word must use letters we have
                word_upper = word.upper()
                word_letters = set(word_upper)
                
                # Skip if word needs letters we don't have (quick check)
                if not word_letters.issubset(rack_set | {'?', '*'}):  # Allow blanks
                    continue
                
                quick_filtered.append(word_upper)
        
        logger.info(f"🤖 Computer player: Quick filtered to {len(quick_filtered)} words")
        
        # First, filter words that can actually be made with our rack
        makeable_words = []
        for word in quick_filtered:
            if self._can_make_word(word, rack_letters):
                makeable_words.append(word)
            
            # Ultra early exit - stop after finding just 10 makeable words
            if len(makeable_words) >= 10:
                logger.info(f"🤖 Computer player: Ultra early exit - found 10 makeable words")
                break
        
        logger.info(f"🤖 Computer player: Found {len(makeable_words)} makeable words")
        
        # Sample from makeable words based on difficulty (ultra aggressive)
        if self.difficulty == "easy":
            sample_size = min(2, len(makeable_words))  # Only 2 words for easy
        elif self.difficulty == "medium":
            sample_size = min(3, len(makeable_words))  # Only 3 words for medium
        else:  # hard
            sample_size = min(5, len(makeable_words))  # Only 5 words for hard
        
        sampled_words = makeable_words[:sample_size]  # Take first N words
        
        logger.info(f"🤖 Computer player: Testing {len(sampled_words)} words: {sampled_words}")
        
        # Try each makeable word
        for word in sampled_words:
            # Try to place the word on the board
            placements = self._find_word_placements_on_board(board, word, rack_letters, language, wordlist)
            
            for placement in placements:
                possible_moves.append({
                    "word": word,
                    "tiles": placement["tiles"],
                    "score": placement.get("points", placement.get("score", 0)),
                    "start_pos": placement["start_pos"],
                    "direction": placement["direction"]
                })
            
            # Ultra early termination: stop as soon as we find 1 valid move
            if len(possible_moves) >= 1:
                logger.info(f"🤖 Computer player: Found move - stopping search immediately")
                break
        
        logger.info(f"🤖 Computer player: Found {len(possible_moves)} total moves")
        
        # Sort by score (best moves first)
        possible_moves.sort(key=lambda x: x["score"], reverse=True)
        
        return possible_moves[:5]  # Return only top 5 moves
    
    def _can_make_word(self, word: str, rack_letters: List[str]) -> bool:
        """Check if a word can be made with the available rack letters."""
        rack_copy = rack_letters.copy()
        
        for letter in word:
            if letter in rack_copy:
                rack_copy.remove(letter)
            elif '?' in rack_copy:  # Blank tile (primary format)
                rack_copy.remove('?')
            elif '*' in rack_copy:  # Blank tile (alternative format)
                rack_copy.remove('*')
            else:
                return False
        
        return True
    
    def _find_word_placements_on_board(self, board: List[List], word: str, rack_letters: List[str], language: str = "en", wordlist: List[str] = None) -> List[Dict[str, Any]]:
        """Find valid placements for a word on the board - only try strategic positions."""
        placements = []
        
        # Get strategic positions where moves are actually possible
        strategic_positions = self._get_strategic_positions(board)
        
        # PERFORMANCE OPTIMIZATION: Limit the number of positions to check
        max_positions = 10  # Only check first 10 strategic positions
        if len(strategic_positions) > max_positions:
            strategic_positions = strategic_positions[:max_positions]
        
        logger.info(f"🤖 Computer AI: Trying '{word}' at {len(strategic_positions)} positions")
        
        # Try each strategic position for both horizontal and vertical placement
        attempts = 0
        max_attempts = 20  # Limit total attempts per word
        
        for row, col in strategic_positions:
            if attempts >= max_attempts:
                logger.info(f"🤖 Computer AI: Max attempts reached for '{word}'")
                break
                
            # Try horizontal placement starting at this position
            if col + len(word) <= 15:  # Word fits horizontally
                attempts += 1
                placement = self._try_placement(board, word, row, col, "horizontal", rack_letters, language, wordlist)
                if placement:
                    logger.info(f"🤖 Computer AI: Found horizontal placement for '{word}' at ({row},{col})")
                    placements.append(placement)
                    # Stop after finding first valid placement for this word
                    return placements
            
            # Try vertical placement starting at this position  
            if row + len(word) <= 15:  # Word fits vertically
                attempts += 1
                placement = self._try_placement(board, word, row, col, "vertical", rack_letters, language, wordlist)
                if placement:
                    logger.info(f"🤖 Computer AI: Found vertical placement for '{word}' at ({row},{col})")
                    placements.append(placement)
                    # Stop after finding first valid placement for this word
                    return placements
        
        if not placements:
            logger.info(f"🤖 Computer AI: No placements found for '{word}' after {attempts} attempts")
        
        return placements
    
    def _get_strategic_positions(self, board: List[List]) -> List[Tuple[int, int]]:
        """Get positions where moves are actually possible (adjacent to existing tiles or center)."""
        strategic_positions = set()
        
        # Check if board is empty (first move)
        board_has_tiles = any(any(cell is not None for cell in row) for row in board)
        
        if not board_has_tiles:
            # First move: only center position matters
            strategic_positions.add((7, 7))
        else:
            # Find positions adjacent to existing tiles (limited for performance)
            tiles_found = 0
            max_tiles_to_check = 5  # Only check first 5 existing tiles
            
            for row in range(15):
                for col in range(15):
                    if board[row][col] is not None:
                        tiles_found += 1
                        if tiles_found > max_tiles_to_check:
                            break
                            
                        # Add only immediate adjacent empty positions
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            adj_row, adj_col = row + dr, col + dc
                            if (0 <= adj_row < 15 and 0 <= adj_col < 15 and 
                                board[adj_row][adj_col] is None):
                                strategic_positions.add((adj_row, adj_col))
                        
                        # Also add the tile position itself (for words that go through existing tiles)
                        strategic_positions.add((row, col))
                
                if tiles_found > max_tiles_to_check:
                    break
        
        result = list(strategic_positions)
        # Limit to first 15 strategic positions for performance
        if len(result) > 15:
            result = result[:15]
            
        logger.info(f"🤖 Computer AI: Found {len(result)} strategic positions")
        return result
    
    def _try_placement(self, board: List[List], word: str, start_row: int, start_col: int, 
                      direction: str, rack_letters: List[str], language: str = "en", wordlist: List[str] = None) -> Optional[Dict[str, Any]]:
        """Try to place a word at a specific position and direction with EFFICIENT validation."""
        tiles = []
        rack_copy = rack_letters.copy()
        
        # Quick validation without expensive GameState creation
        for i, letter in enumerate(word):
            if direction == "horizontal":
                row, col = start_row, start_col + i
            else:  # vertical
                row, col = start_row + i, start_col
            
            if row >= 15 or col >= 15 or row < 0 or col < 0:
                return None
            
            if board[row][col] is not None:
                # Position occupied by existing tile
                if isinstance(board[row][col], dict):
                    existing_letter = board[row][col].get("letter", "").upper()
                else:
                    existing_letter = str(board[row][col]).upper()
                
                if existing_letter != letter.upper():
                    return None
            else:
                # Need to use a letter from rack
                if letter.upper() not in rack_copy:
                    return None
                rack_copy.remove(letter.upper())
                tiles.append((Position(row, col), PlacedTile(letter.upper())))
        
        if not tiles:
            return None
        
        # Basic connectivity check
        if not self._is_connected_to_existing_simple(board, tiles):
            return None
        
        # EFFICIENT FIX: Use actual GameState validation (fast and correct)
        try:
            from app.game_logic.game_state import GameState
            
            # Create minimal GameState for validation
            game_state = GameState(language=language)
            game_state.board = [row[:] for row in board]  # Copy board
            
            # Convert tiles to proper format for validation
            word_positions = [(pos, tile) for pos, tile in tiles]
            
            # Use the actual game validation system (already optimized)
            if isinstance(wordlist, list):
                dictionary = set(wordlist)  # Convert to set for fast lookup
            else:
                dictionary = wordlist or set()
            
            is_valid, error_msg, words_formed = game_state.validate_word_placement(word_positions, dictionary)
            
            if not is_valid:
                logger.info(f"🤖 Computer AI: REJECTED '{word}' - {error_msg}")
                return None
            
        except Exception as e:
            logger.warning(f"🤖 Computer AI: Validation error for '{word}': {e}")
            return None
        
        # Simple scoring calculation
        points = self._calculate_simple_score(word, tiles, board, language)
        
        logger.info(f"🤖 Computer AI: ACCEPTED '{word}' at ({start_row},{start_col}) {direction}: {points} points")
        
        return {
            "word": word,
            "tiles": tiles,
            "points": points,
            "start_pos": (start_row, start_col),
            "direction": direction,
            "words_formed": words_formed if 'words_formed' in locals() else [word]
        }
    

    def _is_connected_to_existing_simple(self, board: List[List], tiles: List[Tuple]) -> bool:
        """Simple connectivity check without expensive validation."""
        # Check if board is empty (first move)
        board_has_tiles = any(any(cell is not None for cell in row) for row in board)
        
        if not board_has_tiles:
            # First move: check if it goes through center
            return any(pos.row == 7 and pos.col == 7 for pos, _ in tiles)
        
        # Check if any new tile is adjacent to existing tiles
        for pos, _ in tiles:
            adjacents = [
                (pos.row-1, pos.col), (pos.row+1, pos.col),
                (pos.row, pos.col-1), (pos.row, pos.col+1)
            ]
            for r, c in adjacents:
                if (0 <= r < 15 and 0 <= c < 15 and board[r][c] is not None):
                    return True
        return False
    
    def _calculate_simple_score(self, word: str, tiles: List[Tuple], board: List[List], language: str = "en") -> int:
        """Simple scoring calculation without expensive GameState operations."""
        from app.game_logic.letter_bag import LETTER_DISTRIBUTION
        
        letter_points = LETTER_DISTRIBUTION.get(language, LETTER_DISTRIBUTION["en"])["points"]
        total_score = 0
        word_multiplier = 1
        
        for pos, tile in tiles:
            # Get base letter points
            points = letter_points.get(tile.letter.upper(), 1)
            
            # Apply simple multipliers based on position
            if pos.row == 7 and pos.col == 7:  # Center
                word_multiplier *= 2
            elif (pos.row + pos.col) % 3 == 0:  # Some premium squares
                points *= 2
            
            total_score += points
        
        total_score *= word_multiplier
        
        # Bonus for using all 7 tiles
        if len(tiles) == 7:
            total_score += 50
            
        return total_score
    
    def _calculate_word_score(self, word: str, tiles: List[Dict], board: List[List], 
                             start_row: int, start_col: int, direction: str, language: str = "en") -> int:
        """Calculate the proper score for a word placement using Scrabble scoring rules."""
        
        # Get letter point values for the language
        letter_points = LETTER_DISTRIBUTION.get(language, LETTER_DISTRIBUTION["en"])["points"]
        
        total_score = 0
        word_multiplier = 1
        
        # Calculate score for each letter in the word
        for i, letter in enumerate(word):
            if direction == "horizontal":
                row, col = start_row, start_col + i
            else:  # vertical
                row, col = start_row + i, start_col
            
            # Get base letter points
            letter_score = letter_points.get(letter.upper(), 1)
            
            # Check if this is a newly placed tile (not already on board)
            is_new_tile = any(tile["row"] == row and tile["col"] == col for tile in tiles)
            
            if is_new_tile:
                # Apply premium squares only to newly placed tiles
                # Note: This is simplified - in real Scrabble, premium squares are more complex
                # For now, we'll apply basic multipliers based on position
                
                # Center square (7,7) is double word score
                if row == 7 and col == 7:
                    word_multiplier *= 2
                
                # Some basic premium square simulation
                # Double letter scores at certain positions
                if (row + col) % 3 == 0 and row != col:
                    letter_score *= 2
                # Triple letter scores at certain positions  
                elif (row + col) % 5 == 0 and row != 7 and col != 7:
                    letter_score *= 3
                # Double word scores at certain positions
                elif row == col and row != 7:
                    word_multiplier *= 2
                # Triple word scores at corners
                elif (row == 0 or row == 14) and (col == 0 or col == 14):
                    word_multiplier *= 3
            
            total_score += letter_score
        
        # Apply word multiplier
        total_score *= word_multiplier
        
        # Bonus for using all 7 tiles (bingo)
        if len(tiles) == 7:
            total_score += 50
        
        return total_score
    
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
    from app.models import Game, Player, User
    
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
    
    # Get computer user
    computer_user = db.query(User).filter(User.username == "computer_player").first()
    if not computer_user:
        raise ValueError("Computer player user not found")
    
    # Create computer player
    computer_player = Player(
        game_id=game_id,
        user_id=computer_user.id,  # Use real computer user ID
        score=0,
        rack=""  # Will be dealt when game starts
    )
    
    db.add(computer_player)
    db.commit()
    db.refresh(computer_player)
    
    logger.info(f"Computer player added to game {game_id} with difficulty {difficulty}")
    
    return {
        "player_id": computer_player.id,
        "user_id": computer_user.id,
        "username": "Computer",
        "display_name": "Computer Player",
        "difficulty": difficulty,
        "is_computer": True
    } 