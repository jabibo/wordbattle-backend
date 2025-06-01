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
    def __init__(self, language: str = "en", test_mode: bool = None):
        self.board = [[None]*15 for _ in range(15)]  # 15x15 board
        self.phase = GamePhase.NOT_STARTED
        self.language = language
        self.letter_bag = create_letter_bag(language, test_mode)
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

    def validate_word_placement(self, word_positions: List[Tuple[Position, PlacedTile]], dictionary: Set[str]) -> Tuple[bool, str]:
        """Validate a word placement according to Scrabble rules."""
        if not word_positions:
            return False, "No tiles were placed. Please place at least one tile to make a move."
            
        # Validate word direction and connectivity
        valid_direction, direction_msg = self._validate_word_direction(word_positions)
        if not valid_direction:
            return False, direction_msg
            
        # Check if it's the first move
        if not self.center_used:
            center_used = any(pos.row == 7 and pos.col == 7 for pos, _ in word_positions)
            if not center_used:
                return False, "The first word must pass through the center star square (H8). Please place at least one tile on the center square."

        # Validate all positions are within bounds
        for pos, tile in word_positions:
            if not (0 <= pos.row < 15 and 0 <= pos.col < 15):
                col_letter = chr(65 + pos.col)
                return False, f"Tile '{tile.letter}' at position ({pos.row + 1}, {col_letter}) is outside the board boundaries. All tiles must be placed within the 15x15 grid."
                
        # Validate no overlapping with existing tiles
        for pos, tile in word_positions:
            if self.board[pos.row][pos.col] is not None:
                existing_tile = self.board[pos.row][pos.col]
                col_letter = chr(65 + pos.col)
                return False, f"Cannot place tile '{tile.letter}' at position ({pos.row + 1}, {col_letter}) - there is already a '{existing_tile.letter}' tile there."

        # Validate all formed words with blank tile handling
        all_words_patterns = self._get_all_formed_words(word_positions)
        if not all_words_patterns:
            if len(word_positions) == 1:
                return False, "Single tile placement must form a word of at least 2 letters by connecting to existing tiles."
            else:
                return False, "The placed tiles do not form any valid words. Make sure tiles are connected and form complete words."
            
        # Check each word pattern against dictionary (handling blank tiles)
        invalid_words = []
        valid_words = []
        for word_pattern in all_words_patterns:
            if self._is_valid_word_pattern(word_pattern, dictionary):
                # Find the actual word that would be formed (for display)
                actual_word = self._resolve_word_pattern(word_pattern, dictionary)
                valid_words.append(actual_word)
            else:
                invalid_words.append(word_pattern)
        
        if invalid_words:
            if len(invalid_words) == 1:
                return False, f"'{invalid_words[0]}' is not a valid word in the dictionary."
            else:
                return False, f"Invalid words formed: {', '.join(invalid_words)}. All words must be valid dictionary words."

        # Validate connection to existing words (except first move)
        if self.center_used and not self._is_connected_to_existing(word_positions):
            return False, "New tiles must connect to existing words on the board. Place at least one tile adjacent to an existing tile."
            
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
        
        return True, success_msg

    def make_move(self, player_id: int, move_type: MoveType, move_data: List[Tuple[Position, PlacedTile]], dictionary: Set[str]) -> Tuple[bool, str, int]:
        """Make a move and return (success, message, points)."""
        if self.phase != GamePhase.IN_PROGRESS:
            if self.phase == GamePhase.NOT_STARTED:
                return False, "Game has not started yet. Please wait for the game to begin.", 0
            elif self.phase == GamePhase.COMPLETED:
                return False, "Game has already ended. No more moves can be made.", 0
            else:
                return False, "Game is not in progress.", 0
        
        if player_id != self.current_player_id:
            return False, f"It's not your turn. Please wait for player {self.current_player_id} to make their move.", 0

        if move_type == MoveType.PASS:
            self._handle_pass(player_id)
            return True, "Turn passed. No tiles placed and no points scored.", 0
        
        elif move_type == MoveType.EXCHANGE:
            if len(self.letter_bag) < 7:
                return False, "Cannot exchange tiles - not enough letters remaining in the bag (need at least 7 letters in bag for exchange).", []
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
            
            success, msg = self.validate_word_placement(move_data, dictionary)
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
    
    def _replenish_rack(self, player_id: int, used_letters: List[str]) -> None:
        """Replenish a player's rack after a move."""
        rack = self.players[player_id]
        for letter in used_letters:
            rack = rack.replace(letter, "", 1)
        
        # Draw new letters
        new_letters = draw_letters(self.letter_bag, 7 - len(rack))
        self.players[player_id] = rack + "".join(new_letters)

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
        """Check if the game has ended and return final scores if it has."""
        if self.phase != GamePhase.IN_PROGRESS:
            return False, None
            
        # Check end conditions
        if len(self.letter_bag) == 0 or len(self.last_moves) >= 6:
            # Game ends if bag is empty or 6 consecutive non-place moves
            recent_moves = self.last_moves[-6:]
            if len(self.letter_bag) == 0 or all(move[1] != MoveType.PLACE for move in recent_moves):
                self.phase = GamePhase.COMPLETED
                final_scores = self._get_final_scores()
                winner_id = max(final_scores.items(), key=lambda x: x[1])[0]
                
                return True, {
                    "final_scores": final_scores,
                    "winner_id": winner_id,
                    "unplayed_penalties": {
                        player_id: sum(LETTER_DISTRIBUTION[self.language]["points"][letter.upper()] for letter in rack)
                        for player_id, rack in self.players.items()
                    }
                }
        
        return False, None

    def _get_final_scores(self) -> Dict:
        """Calculate final scores including unplayed tile penalties."""
        final_scores = self.scores.copy()
        
        # Subtract unplayed tile values
        for player_id, rack in self.players.items():
            penalty = sum(LETTER_DISTRIBUTION[self.language]["points"][letter.upper()] for letter in rack)
            final_scores[player_id] -= penalty
        
        return final_scores 

    def _is_valid_word_pattern(self, word_pattern: str, dictionary: Set[str]) -> bool:
        """Check if a word pattern with potential blank tiles ('?') can form any valid word."""
        if '?' not in word_pattern:
            # No blank tiles, direct dictionary lookup
            return word_pattern.upper() in dictionary
        
        # Has blank tiles - try all possible letter substitutions
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return self._check_pattern_recursive(word_pattern.upper(), dictionary, alphabet, 0)
    
    def _check_pattern_recursive(self, pattern: str, dictionary: Set[str], alphabet: str, pos: int) -> bool:
        """Recursively check if pattern can form valid words by substituting letters for '?'."""
        # Find next '?' in pattern starting from pos
        question_pos = pattern.find('?', pos)
        if question_pos == -1:
            # No more '?' characters, check if current pattern is valid
            return pattern in dictionary
        
        # Try each letter for this '?' position
        for letter in alphabet:
            new_pattern = pattern[:question_pos] + letter + pattern[question_pos + 1:]
            if self._check_pattern_recursive(new_pattern, dictionary, alphabet, question_pos + 1):
                return True
        
        return False
    
    def _resolve_word_pattern(self, word_pattern: str, dictionary: Set[str]) -> str:
        """Find the actual word that a pattern with '?' would form (for display purposes)."""
        if '?' not in word_pattern:
            return word_pattern.upper()
        
        # Find first valid word that matches the pattern
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return self._find_first_valid_word(word_pattern.upper(), dictionary, alphabet, 0)
    
    def _find_first_valid_word(self, pattern: str, dictionary: Set[str], alphabet: str, pos: int) -> str:
        """Find first valid word that matches the pattern."""
        question_pos = pattern.find('?', pos)
        if question_pos == -1:
            return pattern if pattern in dictionary else pattern  # Should be valid if we got here
        
        for letter in alphabet:
            new_pattern = pattern[:question_pos] + letter + pattern[question_pos + 1:]
            if '?' not in new_pattern[question_pos + 1:]:
                # No more '?' after this position
                if new_pattern in dictionary:
                    return new_pattern
            else:
                # More '?' characters to resolve
                result = self._find_first_valid_word(new_pattern, dictionary, alphabet, question_pos + 1)
                if result and result in dictionary:
                    return result
        
        return pattern  # Fallback 