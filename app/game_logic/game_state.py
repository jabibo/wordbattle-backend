from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from .letter_bag import create_letter_bag, draw_letters, return_letters, create_rack, LETTER_DISTRIBUTION
from app.game_logic.board_utils import BOARD_MULTIPLIERS
from app.game_logic.full_points import calculate_full_move_points
import logging
import json
import random
import uuid
import re

logger = logging.getLogger(__name__)

class GamePhase(Enum):
    """Game phase states.
    
    NOT_STARTED: Initial state when game is created but not yet started
    IN_PROGRESS: Game is actively being played
    COMPLETED: Game has finished
    """
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class MoveType(Enum):
    PLACE = "PLACE"
    EXCHANGE = "EXCHANGE"
    PASS = "PASS"

@dataclass(frozen=True)
class Position:
    row: int
    col: int
    
    def __hash__(self):
        return hash((self.row, self.col))
    
    def __eq__(self, other):
        if not isinstance(other, Position):
            return NotImplemented
        return self.row == other.row and self.col == other.col

@dataclass
class PlacedTile:
    letter: str
    is_blank: bool = False
    tile_id: Optional[str] = None
    
    def __post_init__(self):
        """Generate a unique tile ID if not provided."""
        if self.tile_id is None:
            self.tile_id = str(uuid.uuid4())

class GameState:
    def __init__(self, language: str = "en", short_game: bool = None):
        self.board = [[None]*15 for _ in range(15)]  # 15x15 board
        self.phase = GamePhase.NOT_STARTED
        self.language = language
        self.letter_bag = create_letter_bag(language, short_game)
        self.players = {}  # Dict[player_id, List[str]] for racks
        self.scores = {}   # Dict[player_id, int]
        self.bonus_points = {}  # Dict[player_id, int] for end-game bonuses
        self.current_player_id = None
        self.turn_number = 0
        self.consecutive_passes = 0
        # Initialize board multipliers from centralized definition
        self.multipliers = BOARD_MULTIPLIERS
        self.last_moves: List[Tuple[int, MoveType, List[Tuple[Position, PlacedTile]]]] = []  # [(player_id, move_type, move_data)]
        self.center_used = False
        # Add caching for pattern validation
        self._pattern_cache: Dict[str, bool] = {}
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        # Dictionary index by word length for faster lookups
        self._dictionary_by_length: Optional[Dict[int, Set[str]]] = None

    def add_player(self, player_id: int) -> str:
        """Add a player to the game and return their initial rack."""
        if player_id in self.players:
            raise ValueError("Player already in game")
        
        initial_rack = create_rack(self.letter_bag)
        self.players[player_id] = initial_rack
        self.scores[player_id] = 0
        return initial_rack

    def start_game(self, first_player_id: int) -> None:
        """Start the game with the specified first player."""
        if first_player_id not in self.players:
            raise ValueError("First player not in game")
        if len(self.players) < 2:
            raise ValueError("Need at least 2 players to start")
        
        self.current_player_id = first_player_id
        self.phase = GamePhase.IN_PROGRESS

    def validate_word_placement(self, word_positions: List[Tuple[Position, PlacedTile]], dictionary: Set[str]) -> Tuple[bool, str, List[str]]:
        """Validate a word placement according to Scrabble rules. Returns (success, message, words_formed)."""
        if not word_positions:
            return False, "No tiles were placed. Please place at least one tile to make a move.", []
            
        # Validate word direction and connectivity
        valid_direction, direction_msg = self._validate_word_direction(word_positions)
        if not valid_direction:
            return False, direction_msg, []
            
        # Check if it's the first move
        if not self.center_used:
            center_used = any(pos.row == 7 and pos.col == 7 for pos, _ in word_positions)
            if not center_used:
                return False, "The first word must pass through the center star square (H8). Please place at least one tile on the center square.", []
            
        # Validate all positions are within bounds
        for pos, tile in word_positions:
            if not (0 <= pos.row < 15 and 0 <= pos.col < 15):
                col_letter = chr(65 + pos.col)
                return False, f"Tile '{tile.letter}' at position ({pos.row + 1}, {col_letter}) is outside the board boundaries. All tiles must be placed within the 15x15 grid.", []
                
        # Validate no overlapping with existing tiles
        for pos, tile in word_positions:
            if self.board[pos.row][pos.col] is not None:
                existing_tile = self.board[pos.row][pos.col]
                col_letter = chr(65 + pos.col)
                return False, f"Cannot place tile '{tile.letter}' at position ({pos.row + 1}, {col_letter}) - there is already a '{existing_tile.letter}' tile there.", []

        # Validate all formed words with optimized blank tile handling
        all_words_patterns = self._get_all_formed_words(word_positions)
        if not all_words_patterns:
            if len(word_positions) == 1:
                return False, "Single tile placement must form a word of at least 2 letters by connecting to existing tiles.", []
            else:
                return False, "The placed tiles do not form any valid words. Make sure tiles are connected and form complete words.", []
        
        # Batch validate patterns to avoid redundant checks
        unique_patterns = list(set(all_words_patterns))
        pattern_results = {}
        
        # Validate each unique pattern once
        for pattern in unique_patterns:
            pattern_results[pattern] = self._is_valid_word_pattern(pattern, dictionary)
        
        # Check all word patterns against results
        invalid_words = []
        valid_words = []
        for word_pattern in all_words_patterns:
            if pattern_results[word_pattern]:
                # Find the actual word that would be formed (for display)
                actual_word = self._resolve_word_pattern(word_pattern, dictionary)
                valid_words.append(actual_word)
            else:
                invalid_words.append(word_pattern)
        
        if invalid_words:
            if len(invalid_words) == 1:
                return False, f"'{invalid_words[0]}' is not a valid word in the dictionary.", []
            else:
                return False, f"Invalid words formed: {', '.join(invalid_words)}. All words must be valid dictionary words.", []

        # Validate connection to existing words (except first move)
        if self.center_used and not self._is_connected_to_existing(word_positions):
            return False, "New tiles must connect to existing words on the board. Place at least one tile adjacent to an existing tile.", []
            
        # If we get here, the move is valid - provide success message with details
        points = self._calculate_points(word_positions)
        
        # Build success message
        if len(valid_words) == 1:
            word_info = f"Word formed: '{valid_words[0]}'"
        else:
            word_list = "', '".join(valid_words)
            word_info = f"Words formed: '{word_list}'"
        
        bonus_info = ""
        if len(word_positions) == 7:
            bonus_info = " (includes 50-point bonus for using all 7 tiles)"
        
        success_msg = f"Valid move! {word_info}. Points scored: {points}{bonus_info}."
        
        return True, success_msg, valid_words

    def make_move(self, player_id: int, move_type: MoveType, move_data: List[Tuple[Position, PlacedTile]], dictionary: Set[str], skip_turn_validation: bool = False) -> Tuple[bool, str, int]:
        """Make a move and return (success, message, points)."""
        if self.phase != GamePhase.IN_PROGRESS:
            if self.phase == GamePhase.NOT_STARTED:
                return False, "Game has not started yet. Please wait for the game to begin.", 0
            elif self.phase == GamePhase.COMPLETED:
                return False, "Game has already ended. No more moves can be made.", 0
            else:
                return False, "Game is not in progress.", 0
        
        # Turn validation can be bypassed for testing
        if not skip_turn_validation and player_id != self.current_player_id:
            return False, f"It's not your turn. Please wait for player {self.current_player_id} to make their move.", 0

        if move_type == MoveType.PASS:
            self._handle_pass(player_id)
            return True, "Turn passed. No tiles placed and no points scored.", 0
        
        elif move_type == MoveType.EXCHANGE:
            if len(self.letter_bag) < 7:
                return False, "Cannot exchange tiles - not enough letters remaining in the bag (need at least 7 letters in bag for exchange).", []
            if len(move_data) != 7:
                return False, "Cannot exchange tiles - you must exchange exactly 7 letters.", []
            success, msg, new_rack = self._handle_exchange(player_id, move_data)
            if success:
                # Reset consecutive passes since an exchange was made
                self.consecutive_passes = 0
            return success, msg, new_rack
        
        elif move_type == MoveType.PLACE:
            # First validate that player has the required letters in their rack
            rack = self.players[player_id]
            letters_needed = []
            for _, tile in move_data:
                if tile.is_blank:
                    letters_needed.append("?")  # Blank tiles show as "?" in rack
                else:
                    letters_needed.append(tile.letter.upper())
            
            # Check if player has all required letters
            rack_copy = rack
            missing_letters = []
            for letter in letters_needed:
                if letter in rack_copy:
                    rack_copy = rack_copy.replace(letter, "", 1)
                else:
                    missing_letters.append(letter)
            
            if missing_letters:
                if len(missing_letters) == 1:
                    return False, f"You don't have the letter '{missing_letters[0]}' in your rack.", 0
                else:
                    return False, f"You don't have these letters in your rack: {', '.join(missing_letters)}.", 0
            
            success, msg, words_formed = self.validate_word_placement(move_data, dictionary)
            if not success:
                return False, msg, 0
            
            points = self._calculate_points(move_data)
            self._update_board(move_data)
            
            # For blank tiles, we need to remove "?" from rack, not the chosen letter
            letters_to_remove = []
            for _, tile in move_data:
                if tile.is_blank:
                    letters_to_remove.append("?")  # Remove the wildcard from rack
                else:
                    letters_to_remove.append(tile.letter)  # Remove the actual letter
            
            self._replenish_rack(player_id, letters_to_remove)
            self.scores[player_id] += points
            
            # Record move
            self.last_moves.append((player_id, move_type, move_data))
            
            # Reset consecutive passes since a tile was placed
            self.consecutive_passes = 0
            
            # Update center_used flag
            if not self.center_used:
                self.center_used = any(pos.row == 7 and pos.col == 7 for pos, _ in move_data)
            
            self._advance_turn()
            # Return the detailed success message from validation
            return True, msg, points

    def _handle_pass(self, player_id: int) -> None:
        """Handle a pass move."""
        self.last_moves.append((player_id, MoveType.PASS, []))
        self.consecutive_passes += 1
        self._advance_turn()

    def _handle_exchange(self, player_id: int, letters_to_exchange: List[str]) -> Tuple[bool, str, List[str]]:
        """Handle letter exchange move."""
        letters = letters_to_exchange
        rack = self.players[player_id]
        
        # Verify player has these letters and remove them
        missing_letters = []
        for letter in letters:
            if letter not in rack:
                missing_letters.append(letter)
            else:
                rack = rack.replace(letter, "", 1)
        
        if missing_letters:
            if len(missing_letters) == 1:
                return False, f"Cannot exchange '{missing_letters[0]}' - you don't have this letter in your rack.", []
            else:
                return False, f"Cannot exchange letters {', '.join(missing_letters)} - you don't have these letters in your rack.", []
        
        # Perform exchange
        return_letters(self.letter_bag, letters)
        new_letters = draw_letters(self.letter_bag, len(letters))
        
        # Update rack
        rack += "".join(new_letters)
        self.players[player_id] = rack
        
        self.last_moves.append((player_id, MoveType.EXCHANGE, letters_to_exchange))
        self._advance_turn()
        
        # Build success message
        if len(letters) == 1:
            exchange_msg = f"Exchanged 1 letter ('{letters[0]}') for a new letter."
        else:
            letters_str = "', '".join(letters)
            exchange_msg = f"Exchanged {len(letters)} letters ('{letters_str}') for new letters."
        
        return True, exchange_msg, rack

    def _advance_turn(self) -> None:
        """Advance to the next player's turn."""
        player_ids = sorted(self.players.keys())
        current_idx = player_ids.index(self.current_player_id)
        self.current_player_id = player_ids[(current_idx + 1) % len(player_ids)]
        self.turn_number += 1

    def _calculate_points(self, move_data: List[Tuple[Position, PlacedTile]]) -> int:
        """Calculate points for a move."""
        # Get all formed words to properly score including blank tiles
        all_words = self._get_all_formed_words(move_data)
        if not all_words:
            return 0
            
        total_points = 0
        word_multiplier = 1
        
        # For blank tiles, we need to score based on the resolved word
        # Apply temporary move to board to get resolved letters
        board_copy = [[tile for tile in row] for row in self.board]
        for pos, tile in move_data:
            board_copy[pos.row][pos.col] = tile
            
        # Calculate points for each newly placed tile
        move_positions = {(pos.row, pos.col) for pos, _ in move_data}
        
        for pos, tile in move_data:
            if tile.is_blank:
                # Blank tiles are worth 0 points regardless of letter represented
                points = 0
            else:
                # Regular tiles use their letter value
                points = LETTER_DISTRIBUTION[self.language]["points"][tile.letter.upper()]
            
            # Apply letter multipliers only to newly placed tiles
            if (pos.row, pos.col) in self.multipliers:
                multi = self.multipliers[(pos.row, pos.col)]
                if multi == "BL":  # Double letter score
                    points *= 2
                elif multi == "BW":  # Triple letter score
                    points *= 3
                elif multi == "WL":  # Double word score
                    word_multiplier *= 2
                elif multi == "WW":  # Triple word score
                    word_multiplier *= 3
            
            total_points += points
        
        # Apply word multiplier
        total_points *= word_multiplier
        
        # Bonus for using all 7 letters
        if len(move_data) == 7:
            total_points += 50
            
        return total_points

    def calculate_detailed_score_breakdown(self, move_data: List[Tuple[Position, PlacedTile]]) -> Dict:
        """Calculate detailed score breakdown with word-by-word and letter-by-letter analysis."""
        logger.info(f"🔍 Calculating detailed score breakdown for {len(move_data)} tiles")
        
        # Get all formed words to properly score
        all_words = self._get_all_formed_words(move_data)
        logger.info(f"🔍 Found {len(all_words)} words: {all_words}")
        
        if not all_words:
            logger.warning("🔍 No words formed - returning empty breakdown")
            return {
                "total_points": 0,
                "words_formed": [],
                "bonus_points": [],
                "grand_total": 0
            }
            
        # Apply temporary move to board to get resolved letters and coordinates
        board_copy = [[tile for tile in row] for row in self.board]
        for pos, tile in move_data:
            board_copy[pos.row][pos.col] = tile
            
        move_positions = {(pos.row, pos.col) for pos, _ in move_data}
        words_formed = []
        total_base_points = 0
        
        # Process each word formed
        for word in all_words:
            word_positions = self._get_word_positions(word, board_copy)
            if not word_positions:
                continue
                
            letters_detail = []
            word_base_score = 0
            word_multipliers = []
            
            # Calculate letter-by-letter breakdown for this word
            for row, col in word_positions:
                tile = board_copy[row][col]
                is_newly_placed = (row, col) in move_positions
                
                # Get base letter value
                if tile.is_blank:
                    base_value = 0
                else:
                    base_value = LETTER_DISTRIBUTION[self.language]["points"][tile.letter.upper()]
                
                letter_multiplier = None
                letter_multiplier_value = 1
                
                # Apply multipliers only to newly placed tiles
                if is_newly_placed and (row, col) in self.multipliers:
                    multiplier_type = self.multipliers[(row, col)]
                    if multiplier_type == "BL":  # Double letter score
                        letter_multiplier = "double_letter"
                        letter_multiplier_value = 2
                    elif multiplier_type == "BW":  # Triple letter score
                        letter_multiplier = "triple_letter"
                        letter_multiplier_value = 3
                    elif multiplier_type == "WL":  # Double word score
                        word_multipliers.append({"type": "double_word", "value": 2})
                    elif multiplier_type == "WW":  # Triple word score
                        word_multipliers.append({"type": "triple_word", "value": 3})
                
                final_value = base_value * letter_multiplier_value
                word_base_score += final_value
                
                letters_detail.append({
                    "letter": tile.letter.upper(),
                    "position": {"row": row, "col": col},
                    "base_value": base_value,
                    "final_value": final_value,
                    "multiplier": letter_multiplier,
                    "is_newly_placed": is_newly_placed,
                    "is_blank": tile.is_blank
                })
            
            # Apply word multipliers
            word_multiplier_total = 1
            for multiplier in word_multipliers:
                word_multiplier_total *= multiplier["value"]
            
            word_final_score = word_base_score * word_multiplier_total
            total_base_points += word_final_score
            
            words_formed.append({
                "word": word,
                "letters": letters_detail,
                "base_score": word_base_score,
                "word_multipliers": word_multipliers,
                "final_score": word_final_score
            })
        
        # Calculate bonus points
        bonus_points = []
        grand_total = total_base_points
        
        if len(move_data) == 7:
            bonus_points.append({
                "type": "seven_tiles",
                "description": "Used all 7 tiles",
                "points": 50
            })
            grand_total += 50
        
        return {
            "total_points": total_base_points,
            "words_formed": words_formed,
            "bonus_points": bonus_points,
            "grand_total": grand_total
        }

    def _get_word_positions(self, word: str, board: List[List[Optional[PlacedTile]]]) -> List[Tuple[int, int]]:
        """Find the positions of a word on the board."""
        word = word.upper()
        
        # Search horizontally
        for row in range(15):
            for col in range(15 - len(word) + 1):
                positions = []
                current_word = ""
                
                for i in range(len(word)):
                    if board[row][col + i] is not None:
                        letter = board[row][col + i].letter.upper()
                        current_word += letter
                        positions.append((row, col + i))
                    else:
                        break
                
                if current_word == word and len(positions) == len(word):
                    # Check if this is a complete word (not part of a longer word)
                    if ((col == 0 or board[row][col - 1] is None) and 
                        (col + len(word) == 15 or board[row][col + len(word)] is None)):
                        return positions
        
        # Search vertically
        for col in range(15):
            for row in range(15 - len(word) + 1):
                positions = []
                current_word = ""
                
                for i in range(len(word)):
                    if board[row + i][col] is not None:
                        letter = board[row + i][col].letter.upper()
                        current_word += letter
                        positions.append((row + i, col))
                    else:
                        break
                
                if current_word == word and len(positions) == len(word):
                    # Check if this is a complete word (not part of a longer word)
                    if ((row == 0 or board[row - 1][col] is None) and 
                        (row + len(word) == 15 or board[row + len(word)][col] is None)):
                        return positions
        
        return []

    def _replenish_rack(self, player_id: int, used_letters: List[str]) -> None:
        """Replenish a player's rack after a move.
        
        If the bag is empty, no new tiles are distributed.
        This can lead to players having fewer than 7 tiles, which is expected endgame behavior.
        """
        rack = self.players[player_id]
        for letter in used_letters:
            rack = rack.replace(letter, "", 1)
        
        # Only draw new letters if bag has tiles available
        if len(self.letter_bag) > 0:
            tiles_needed = 7 - len(rack)
            new_letters = draw_letters(self.letter_bag, tiles_needed)
            self.players[player_id] = rack + "".join(new_letters)
        else:
            # Bag is empty - player keeps current rack without replenishment
            self.players[player_id] = rack
            logger.info(f"🎯 Bag is empty - Player {player_id} now has {len(rack)} tiles (no replenishment possible)")

    def _is_connected_to_existing(self, word_positions: List[Tuple[Position, PlacedTile]]) -> bool:
        """Check if the word connects to existing tiles on the board."""
        for pos, _ in word_positions:
            # Check adjacent positions
            adjacents = [
                (pos.row-1, pos.col), (pos.row+1, pos.col),
                (pos.row, pos.col-1), (pos.row, pos.col+1)
            ]
            for r, c in adjacents:
                if (0 <= r < 15 and 0 <= c < 15 and 
                    self.board[r][c] is not None and 
                    (r, c) not in [(p.row, p.col) for p, _ in word_positions]):
                    return True
        return False

    def _get_all_formed_words(self, word_positions: List[Tuple[Position, PlacedTile]]) -> List[str]:
        """Get all words formed by a move, including cross-words."""
        if not word_positions:
            return []

        words = []
        board_copy = [[tile for tile in row] for row in self.board]
        
        # Apply new tiles to temporary board
        for pos, tile in word_positions:
            board_copy[pos.row][pos.col] = tile
        
        # Determine word direction
        if len(word_positions) == 1:
            # Single letter case - check both directions
            horizontal_word = self._find_words_at_position(
                word_positions[0][0].row,
                word_positions[0][0].col,
                board_copy,
                True
            )
            vertical_word = self._find_words_at_position(
                word_positions[0][0].row,
                word_positions[0][0].col,
                board_copy,
                False
            )
            words.extend(horizontal_word + vertical_word)
        else:
            # Multiple letters - determine direction
            is_horizontal = word_positions[0][0].row == word_positions[1][0].row
            
            # Find the main word
            main_word_row = word_positions[0][0].row
            main_word_col = word_positions[0][0].col
            main_word = self._find_words_at_position(
                main_word_row,
                main_word_col,
                board_copy,
                is_horizontal
            )
            words.extend(main_word)
            
            # Find all cross-words
            for pos, _ in word_positions:
                cross_word = self._find_words_at_position(
                    pos.row,
                    pos.col,
                    board_copy,
                    not is_horizontal  # Opposite direction of main word
                )
                words.extend(cross_word)
        
        # Filter out single letters and duplicates
        return list(set(word for word in words if len(word) > 1))
    
    def _find_words_at_position(self, row: int, col: int, board: List[List[Optional[PlacedTile]]], is_horizontal: bool) -> List[str]:
        """Find words that include the tile at the given position in the specified direction."""
        if not (0 <= row < 15 and 0 <= col < 15) or board[row][col] is None:
            return []
        
        # Find start of word
        start_row, start_col = row, col
        while True:
            prev_row = start_row - (0 if is_horizontal else 1)
            prev_col = start_col - (1 if is_horizontal else 0)
            
            if not (0 <= prev_row < 15 and 0 <= prev_col < 15):
                break
                
            if board[prev_row][prev_col] is None:
                break
                
            start_row, start_col = prev_row, prev_col
        
        # Build word by scanning forward
        word = []
        current_row, current_col = start_row, start_col
        
        while True:
            if not (0 <= current_row < 15 and 0 <= current_col < 15):
                break
                
            current_tile = board[current_row][current_col]
            if current_tile is None:
                break
                
            # For blank tiles, preserve the '?' character for pattern matching
            # For regular tiles, use the letter
            if current_tile.is_blank and current_tile.letter == "?":
                word.append("?")
            else:
                word.append(current_tile.letter.upper())
            
            current_row += 0 if is_horizontal else 1
            current_col += 1 if is_horizontal else 0
        
        return ["".join(word)] if len(word) > 1 else []

    def _validate_word_direction(self, word_positions: List[Tuple[Position, PlacedTile]]) -> Tuple[bool, str]:
        """Validate that all tiles are placed in a single line and form a connected word with existing tiles."""
        if len(word_positions) <= 1:
            return True, ""
            
        # Determine direction from first two tiles
        is_horizontal = word_positions[0][0].row == word_positions[1][0].row
        reference = word_positions[0][0].row if is_horizontal else word_positions[0][0].col
        
        # Check all tiles are in the same line
        for pos, tile in word_positions[1:]:
            current = pos.row if is_horizontal else pos.col
            if current != reference:
                direction = "row" if is_horizontal else "column"
                return False, f"All tiles must be placed in a single {direction}. Found tiles in different {direction}s - please place all tiles either horizontally in one row or vertically in one column."
        
        # Check that new tiles form a connected word when combined with existing board tiles
        # Create a temporary board with the new tiles
        board_copy = [[tile for tile in row] for row in self.board]
        for pos, tile in word_positions:
            board_copy[pos.row][pos.col] = tile
        
        # Get all positions in the word direction
        positions = sorted(
            [(pos.col if is_horizontal else pos.row) for pos, _ in word_positions]
        )
        
        # Find the complete word span including existing tiles
        start_pos = positions[0]
        end_pos = positions[-1]
        
        # Extend backwards to find start of complete word
        while True:
            prev_pos = start_pos - 1
            if is_horizontal:
                if prev_pos < 0 or board_copy[reference][prev_pos] is None:
                    break
            else:
                if prev_pos < 0 or board_copy[prev_pos][reference] is None:
                    break
            start_pos = prev_pos
        
        # Extend forwards to find end of complete word
        while True:
            next_pos = end_pos + 1
            if is_horizontal:
                if next_pos >= 15 or board_copy[reference][next_pos] is None:
                    break
            else:
                if next_pos >= 15 or board_copy[next_pos][reference] is None:
                    break
            end_pos = next_pos
        
        # Check that all positions from start to end have tiles (no gaps)
        gap_positions = []
        for pos in range(start_pos, end_pos + 1):
            if is_horizontal:
                if board_copy[reference][pos] is None:
                    gap_positions.append(pos)
            else:
                if board_copy[pos][reference] is None:
                    gap_positions.append(pos)
        
        if gap_positions:
            direction = "horizontally" if is_horizontal else "vertically"
            if len(gap_positions) == 1:
                gap_desc = f"position {gap_positions[0] + 1}"
            else:
                gap_desc = f"positions {', '.join(str(p + 1) for p in gap_positions)}"
            return False, f"Tiles must form a connected word {direction}. There are gaps at {gap_desc} - either fill the gaps with tiles or place tiles adjacent to each other."
        
        return True, ""

    def _update_board(self, move_data: List[Tuple[Position, PlacedTile]]) -> None:
        """Update the board with new tiles."""
        for pos, tile in move_data:
            self.board[pos.row][pos.col] = tile

    def check_game_end(self) -> Tuple[bool, Optional[Dict]]:
        """Check if the game has ended and return final scores with winner information."""
        if self.phase != GamePhase.IN_PROGRESS:
            return False, None
        
        num_players = len(self.players)
        end_reason = None
        empty_rack_player = None
        
        # Rule 1: Check if any player has emptied their rack
        for player_id, rack in self.players.items():
            if len(rack) == 0:
                empty_rack_player = player_id
                end_reason = "empty_rack"
                break
        
        # Rule 2: Check if all players have passed 3 times (total passes = 3 * num_players)
        if not end_reason and self.consecutive_passes >= (3 * num_players):
            end_reason = "all_players_passed_three_times"
        
        # Rule 3: If bag is empty and someone tried to draw but couldn't, this gets handled in replenish_rack
        # The empty rack check above will catch when someone finishes their last tiles
        
        if end_reason:
            self.phase = GamePhase.COMPLETED
            
            # Calculate final scores with proper bonuses
            final_scores = self.scores.copy()
            unplayed_penalties = {}
            empty_rack_bonus = 0
            
            # Calculate unplayed tile penalties and bonus for empty rack winner
            for player_id, rack in self.players.items():
                penalty = sum(LETTER_DISTRIBUTION[self.language]["points"].get(letter.upper(), 0) for letter in rack)
                unplayed_penalties[player_id] = penalty
                
                if player_id == empty_rack_player:
                    # Player who emptied rack gets bonus from all other players' remaining tiles
                    empty_rack_bonus += penalty  # Add their own penalty back (they don't lose points)
                else:
                    # Other players lose points for remaining tiles
                    final_scores[player_id] -= penalty
                    if empty_rack_player:
                        # Add their penalty to the empty rack player's bonus
                        empty_rack_bonus += penalty
            
            # Apply empty rack bonus
            if empty_rack_player and empty_rack_bonus > 0:
                final_scores[empty_rack_player] += empty_rack_bonus
            
            # Determine winner
            winner_id = max(final_scores.items(), key=lambda x: x[1])[0]
            winner_score = final_scores[winner_id]
            
            # Create completion details with clear winner message
            completion_details = {
                "final_scores": final_scores,
                "winner_id": winner_id,
                "winner_score": winner_score,
                "end_reason": end_reason,
                "unplayed_penalties": unplayed_penalties,
                "message": self._get_game_end_message(end_reason, winner_id, winner_score, empty_rack_player, empty_rack_bonus)
            }
            
            if empty_rack_player:
                completion_details["empty_rack_player"] = empty_rack_player
                completion_details["empty_rack_bonus"] = empty_rack_bonus
            
            return True, completion_details
        
        return False, None
    
    def _get_game_end_message(self, end_reason: str, winner_id: int, winner_score: int, empty_rack_player: int = None, empty_rack_bonus: int = 0) -> str:
        """Generate a clear game end message announcing the winner."""
        
        if end_reason == "empty_rack":
            if empty_rack_bonus > 0:
                return f"🎉 GAME OVER! Player {winner_id} wins with {winner_score} points! They emptied their rack and earned {empty_rack_bonus} bonus points from remaining tiles."
            else:
                return f"🎉 GAME OVER! Player {winner_id} wins with {winner_score} points! They emptied their rack first."
        
        elif end_reason == "all_players_passed_three_times":
            return f"🎉 GAME OVER! All players passed 3 times. Player {winner_id} wins with {winner_score} points!"
        
        else:
            return f"🎉 GAME OVER! Player {winner_id} wins with {winner_score} points!"

    def _get_final_scores(self) -> Dict:
        """Calculate final scores including unplayed tile penalties."""
        # This method is now incorporated into check_game_end for better control
        final_scores = self.scores.copy()
        
        # Subtract unplayed tile values (basic version - check_game_end has the complete logic)
        for player_id, rack in self.players.items():
            penalty = sum(LETTER_DISTRIBUTION[self.language]["points"].get(letter.upper(), 0) for letter in rack)
            final_scores[player_id] -= penalty
        
        return final_scores

    def _get_dictionary_by_length(self, dictionary: Set[str]) -> Dict[int, Set[str]]:
        """Create or get a dictionary indexed by word length for faster lookups."""
        if self._dictionary_by_length is None:
            self._dictionary_by_length = {}
            for word in dictionary:
                length = len(word)
                if length not in self._dictionary_by_length:
                    self._dictionary_by_length[length] = set()
                self._dictionary_by_length[length].add(word)
        return self._dictionary_by_length

    def _is_valid_word_pattern(self, word_pattern: str, dictionary: Set[str]) -> bool:
        """Check if a word pattern with potential blank tiles ('?') can form any valid word.
        
        Optimized version using regex patterns and caching for much better performance.
        """
        if '?' not in word_pattern:
            # No blank tiles, direct dictionary lookup
            return word_pattern.upper() in dictionary
        
        # Check cache first
        cache_key = word_pattern.upper()
        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]
        
        pattern_upper = word_pattern.upper()
        
        # Get words of the same length only (major optimization)
        dictionary_by_length = self._get_dictionary_by_length(dictionary)
        words_of_length = dictionary_by_length.get(len(pattern_upper), set())
        
        if not words_of_length:
            self._pattern_cache[cache_key] = False
            return False
        
        # Create regex pattern for fast matching
        regex_pattern = self._get_or_create_regex_pattern(pattern_upper)
        
        # Find matching words using compiled regex on subset
        found_match = False
        for word in words_of_length:
            if regex_pattern.match(word):
                found_match = True
                break  # Early termination - just need one match
        
        # Cache the result
        self._pattern_cache[cache_key] = found_match
        return found_match
    
    def _get_or_create_regex_pattern(self, pattern: str) -> re.Pattern:
        """Get or create a compiled regex pattern for the given word pattern."""
        if pattern not in self._compiled_patterns:
            # Convert '?' to regex pattern that matches any letter
            regex_str = pattern.replace('?', '[A-Z]')
            regex_str = f'^{regex_str}$'  # Exact match
            self._compiled_patterns[pattern] = re.compile(regex_str)
        
        return self._compiled_patterns[pattern]
    
    def _resolve_word_pattern(self, word_pattern: str, dictionary: Set[str]) -> str:
        """Find the actual word that a pattern with '?' would form (for display purposes).
        
        Optimized version using regex patterns.
        """
        if '?' not in word_pattern:
            return word_pattern.upper()
        
        pattern_upper = word_pattern.upper()
        
        # Get words of the same length only
        dictionary_by_length = self._get_dictionary_by_length(dictionary)
        words_of_length = dictionary_by_length.get(len(pattern_upper), set())
        
        if not words_of_length:
            return pattern_upper
        
        regex_pattern = self._get_or_create_regex_pattern(pattern_upper)
        
        # Find first matching word
        for word in words_of_length:
            if regex_pattern.match(word):
                return word
        
        return pattern_upper  # Fallback (shouldn't happen if validation passed)

    def _clear_validation_caches(self) -> None:
        """Clear validation caches to manage memory usage.
        
        Call this periodically if memory usage becomes a concern.
        """
        self._pattern_cache.clear()
        self._compiled_patterns.clear()
        self._dictionary_by_length = None 