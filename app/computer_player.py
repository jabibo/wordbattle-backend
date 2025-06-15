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
            # Parse game state
            board = game_state_data.get("board", [[None for _ in range(15)] for _ in range(15)])
            language = game_state_data.get("language", "en")
            
            # Convert rack string to list
            rack_letters = list(rack)
            
            # Debug: Log board format
            tiles_on_board = 0
            for row in board:
                for cell in row:
                    if cell is not None:
                        tiles_on_board += 1
                        if tiles_on_board <= 3:  # Log first few tiles for debugging
                            logger.info(f"Computer player: Board cell example: {cell} (type: {type(cell)})")
            
            # Check if board is empty (first move)
            board_is_empty = tiles_on_board == 0
            logger.info(f"Computer player: Board has {tiles_on_board} tiles, Rack: {rack_letters}, Language: {language}")
            logger.info(f"Computer player: Wordlist size: {len(wordlist)}")
            
            # Test if we can make some basic words
            test_words = ["KRAFT", "FAKT", "TRAF"]
            for test_word in test_words:
                if test_word in wordlist:
                    can_make = self._can_make_word(test_word, rack_letters)
                    logger.info(f"Computer player: Can make '{test_word}': {can_make}")
                else:
                    logger.info(f"Computer player: '{test_word}' not in wordlist")
            
            # Find possible word placements
            possible_moves = self._find_possible_moves(board, rack_letters, wordlist, language)
            
            logger.info(f"Computer player: Found {len(possible_moves)} possible moves")
            if possible_moves:
                logger.info(f"Computer player: Top 3 moves: {possible_moves[:3]}")
            
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
    
    def _find_possible_moves(self, board: List[List], rack_letters: List[str], wordlist: List[str], language: str = "en") -> List[Dict[str, Any]]:
        """Find all possible moves for the current board state and rack."""
        possible_moves = []
        
        logger.info(f"Computer player: Starting move search with rack {rack_letters}")
        
        # First, filter words that can actually be made with our rack
        # This is much more efficient than random sampling
        makeable_words = []
        for word in wordlist:
            if len(word) < 2 or len(word) > 7:  # Reasonable word length limits
                continue
            if self._can_make_word(word.upper(), rack_letters):
                makeable_words.append(word.upper())
        
        logger.info(f"Computer player: Found {len(makeable_words)} words that can be made from rack")
        
        # Sample from makeable words based on difficulty (reduced for performance)
        if self.difficulty == "easy":
            sample_size = min(5, len(makeable_words))  # Very aggressive reduction
        elif self.difficulty == "medium":
            sample_size = min(8, len(makeable_words))  # Very aggressive reduction
        else:  # hard
            sample_size = min(12, len(makeable_words))  # Very aggressive reduction
        
        if len(makeable_words) > sample_size:
            # Prioritize longer words (they typically score more)
            makeable_words.sort(key=len, reverse=True)
            sampled_words = makeable_words[:sample_size//2]  # Take top half by length
            # Add random selection from remaining words
            remaining_words = makeable_words[sample_size//2:]
            if remaining_words:
                sampled_words.extend(random.sample(remaining_words, min(sample_size//2, len(remaining_words))))
        else:
            sampled_words = makeable_words
        
        logger.info(f"Computer player: Testing {len(sampled_words)} makeable words")
        
        # Track what we're testing for debugging
        words_with_placements = 0
        
        # Try each makeable word
        for word in sampled_words:
            # Try to place the word on the board
            placements = self._find_word_placements_on_board(board, word, rack_letters, language, wordlist)
            
            if placements:
                words_with_placements += 1
                # Log the first few successful placements
                if words_with_placements <= 5:
                    logger.info(f"Computer player: Found {len(placements)} placements for '{word}' (score: {placements[0]['score']})")
            
            for placement in placements:
                possible_moves.append({
                    "word": word,
                    "tiles": placement["tiles"],
                    "score": placement["score"],
                    "start_pos": placement["start_pos"],
                    "direction": placement["direction"]
                })
            
            # Early termination: if we have enough good moves, stop searching
            if len(possible_moves) >= 3:  # Stop when we have just 3 valid moves (much more aggressive)
                logger.info(f"Computer player: Early termination - found {len(possible_moves)} moves")
                break
        
        logger.info(f"Computer player: Found {len(possible_moves)} total possible moves from {words_with_placements} words")
        
        # Sort by score (best moves first)
        possible_moves.sort(key=lambda x: x["score"], reverse=True)
        
        return possible_moves[:50]  # Limit to top 50 moves for performance
    
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
        
        logger.info(f"Computer AI: Trying to place '{word}' at {len(strategic_positions)} strategic positions")
        
        # Try each strategic position for both horizontal and vertical placement
        attempts = 0
        for row, col in strategic_positions:
            # Try horizontal placement starting at this position
            if col + len(word) <= 15:  # Word fits horizontally
                attempts += 1
                placement = self._try_placement(board, word, row, col, "horizontal", rack_letters, language, wordlist)
                if placement:
                    logger.info(f"Computer AI: Found valid horizontal placement for '{word}' at ({row},{col})")
                    placements.append(placement)
            
            # Try vertical placement starting at this position  
            if row + len(word) <= 15:  # Word fits vertically
                attempts += 1
                placement = self._try_placement(board, word, row, col, "vertical", rack_letters, language, wordlist)
                if placement:
                    logger.info(f"Computer AI: Found valid vertical placement for '{word}' at ({row},{col})")
                    placements.append(placement)
            
            # Also try placing word so it ENDS at this strategic position
            # Horizontal (word ends at strategic position)
            start_col = col - len(word) + 1
            if start_col >= 0:
                attempts += 1
                placement = self._try_placement(board, word, row, start_col, "horizontal", rack_letters, language, wordlist)
                if placement:
                    logger.info(f"Computer AI: Found valid horizontal placement (ending) for '{word}' at ({row},{start_col})")
                    placements.append(placement)
            
            # Vertical (word ends at strategic position)
            start_row = row - len(word) + 1
            if start_row >= 0:
                attempts += 1
                placement = self._try_placement(board, word, start_row, col, "vertical", rack_letters, language, wordlist)
                if placement:
                    logger.info(f"Computer AI: Found valid vertical placement (ending) for '{word}' at ({start_row},{col})")
                    placements.append(placement)
        
        if not placements and attempts > 0:
            logger.info(f"Computer AI: No valid placements found for '{word}' after {attempts} attempts")
        
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
            # Find all positions adjacent to existing tiles
            for row in range(15):
                for col in range(15):
                    if board[row][col] is not None:
                        # Add all adjacent empty positions
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            adj_row, adj_col = row + dr, col + dc
                            if (0 <= adj_row < 15 and 0 <= adj_col < 15 and 
                                board[adj_row][adj_col] is None):
                                strategic_positions.add((adj_row, adj_col))
                        
                        # Also add the tile position itself (for words that go through existing tiles)
                        strategic_positions.add((row, col))
        
        result = list(strategic_positions)
        logger.info(f"Computer AI: Found {len(result)} strategic positions on board: {result[:10]}{'...' if len(result) > 10 else ''}")
        return result
    
    def _try_placement(self, board: List[List], word: str, start_row: int, start_col: int, 
                      direction: str, rack_letters: List[str], language: str = "en", wordlist: List[str] = None) -> Optional[Dict[str, Any]]:
        """Try to place a word at a specific position and direction using standard validation."""
        tiles = []
        rack_copy = rack_letters.copy()
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
                # Handle both simple letter format and complex tile object format
                if isinstance(existing_tile, dict):
                    # New format: {"letter": "A", "is_blank": false, "tile_id": "..."}
                    existing_letter = existing_tile.get("letter")
                else:
                    # Old format: just the letter string
                    existing_letter = existing_tile
                
                # Letter already on board - must match
                if existing_letter != letter:
                    return None
                touches_existing = True
            else:
                # Need to place a tile from rack
                if letter in rack_copy:
                    rack_copy.remove(letter)
                elif '?' in rack_copy:  # Blank tile (using ? instead of *)
                    rack_copy.remove('?')
                elif '*' in rack_copy:  # Also support * for blank tiles
                    rack_copy.remove('*')
                else:
                    return None
                
                tiles.append({
                    "row": row,
                    "col": col,
                    "letter": letter
                })
        
        # Must touch at least one existing tile (except for first move)
        board_has_tiles = False
        for row in board:
            for cell in row:
                if cell is not None:
                    board_has_tiles = True
                    break
            if board_has_tiles:
                break
        
        if not touches_existing and board_has_tiles:
            return None
        
        # First move must go through center (7,7)
        if not board_has_tiles:
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
        
        # *** USE STANDARD VALIDATION FROM GAME_STATE ***
        # Create a temporary game state for validation
        try:
            from app.game_logic.game_state import GameState, Position, PlacedTile
            
            # Convert wordlist to dictionary set
            if wordlist is None:
                logger.error(f"Computer AI: No wordlist provided for validation")
                return None
            dictionary = set(word.upper() for word in wordlist)
            
            # Create temporary game state with current board
            temp_game_state = GameState(language=language)
            
            # Convert board format for game state
            # Handle both tile objects and simple letters
            temp_game_state.board = [[None for _ in range(15)] for _ in range(15)]
            for row_idx, row in enumerate(board):
                for col_idx, cell in enumerate(row):
                    if cell is not None:
                        if isinstance(cell, dict):
                            # Convert dict format to PlacedTile
                            temp_game_state.board[row_idx][col_idx] = PlacedTile(
                                letter=cell.get("letter", ""),
                                is_blank=cell.get("is_blank", False),
                                tile_id=cell.get("tile_id")
                            )
                        else:
                            # Convert simple letter to PlacedTile
                            temp_game_state.board[row_idx][col_idx] = PlacedTile(
                                letter=str(cell),
                                is_blank=False
                            )
            
            # Convert move data to the format expected by game state validation
            word_positions = []
            for tile in tiles:
                pos = Position(row=tile["row"], col=tile["col"])
                placed_tile = PlacedTile(
                    letter=tile["letter"],
                    is_blank=False  # For now, computer doesn't use blank tiles
                )
                word_positions.append((pos, placed_tile))
            
            # Use the proper game state validation method
            is_valid, error_msg, words_formed = temp_game_state.validate_word_placement(word_positions, dictionary)
            
            if not is_valid:
                logger.debug(f"Computer AI: Move rejected by game state validation: {error_msg}")
                return None
            
            logger.debug(f"Computer AI: Move validated successfully, words formed: {words_formed}")
            
        except Exception as e:
            logger.error(f"Computer AI: Error in game state validation: {e}")
            return None  # Reject move if validation fails
        
        # Calculate proper score using letter point values
        score = self._calculate_word_score(word, tiles, board, start_row, start_col, direction, language)
        
        return {
            "tiles": tiles,
            "score": score,
            "start_pos": (start_row, start_col),
            "direction": direction
        }
    
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