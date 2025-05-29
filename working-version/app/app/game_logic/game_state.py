from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from .letter_bag import create_letter_bag, draw_letters, return_letters, create_rack, LETTER_DISTRIBUTION
from app.game_logic.board_utils import BOARD_MULTIPLIERS
from app.game_logic.full_points import calculate_full_move_points
import logging
import json
import random

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

class GameState:
    def __init__(self, language: str = "en"):
        self.board = [[None]*15 for _ in range(15)]  # 15x15 board
        self.phase = GamePhase.NOT_STARTED
        self.language = language
        self.letter_bag = create_letter_bag(language)
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
            return False, "No tiles placed"
            
        # Validate word direction and connectivity
        valid_direction, direction_msg = self._validate_word_direction(word_positions)
        if not valid_direction:
            return False, direction_msg
            
        # Check if it's the first move
        if not self.center_used:
            center_used = any(pos.row == 7 and pos.col == 7 for pos, _ in word_positions)
            if not center_used:
                return False, "First word must use center square"

        # Validate all formed words
        all_words = self._get_all_formed_words(word_positions)
        if not all_words:
            return False, "No valid words formed"
            
        for word in all_words:
            if word.upper() not in dictionary:
                return False, f"Invalid word: {word}"

        # Validate connection to existing words (except first move)
        if self.center_used and not self._is_connected_to_existing(word_positions):
            return False, "Word must connect to existing tiles"
            
        # Validate all positions are within bounds
        for pos, _ in word_positions:
            if not (0 <= pos.row < 15 and 0 <= pos.col < 15):
                return False, "Word placement out of bounds"
                
        # Validate no overlapping with existing tiles
        for pos, _ in word_positions:
            if self.board[pos.row][pos.col] is not None:
                return False, "Cannot place tiles over existing tiles"

        return True, ""

    def make_move(self, player_id: int, move_type: MoveType, move_data: List[Tuple[Position, PlacedTile]], dictionary: Set[str]) -> Tuple[bool, str, int]:
        """Make a move and return (success, message, points)."""
        if self.phase != GamePhase.IN_PROGRESS:
            return False, "Game not in progress", 0
        
        if player_id != self.current_player_id:
            return False, "Not your turn", 0

        if move_type == MoveType.PASS:
            self._handle_pass(player_id)
            return True, "Pass successful", 0
        
        elif move_type == MoveType.EXCHANGE:
            if len(self.letter_bag) < 7:
                return False, "Not enough letters in bag for exchange", []
            success, msg, new_rack = self._handle_exchange(player_id, move_data)
            if success:
                # Reset consecutive passes since an exchange was made
                self.consecutive_passes = 0
            return success, msg, new_rack
        
        elif move_type == MoveType.PLACE:
            success, msg = self.validate_word_placement(move_data, dictionary)
            if not success:
                return False, msg, 0
            
            points = self._calculate_points(move_data)
            self._update_board(move_data)
            self._replenish_rack(player_id, [tile.letter for _, tile in move_data])
            self.scores[player_id] += points
            
            # Record move
            self.last_moves.append((player_id, move_type, move_data))
            
            # Reset consecutive passes since a tile was placed
            self.consecutive_passes = 0
            
            # Update center_used flag
            if not self.center_used:
                self.center_used = any(pos.row == 7 and pos.col == 7 for pos, _ in move_data)
            
            self._advance_turn()
            return True, "Move successful", points

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
        for letter in letters:
            if letter not in rack:
                return False, "Cannot exchange letters you don't have", []
            rack = rack.replace(letter, "", 1)
        
        # Perform exchange
        return_letters(self.letter_bag, letters)
        new_letters = draw_letters(self.letter_bag, len(letters))
        
        # Update rack
        rack += "".join(new_letters)
        self.players[player_id] = rack
        
        self.last_moves.append((player_id, MoveType.EXCHANGE, letters_to_exchange))
        self._advance_turn()
        return True, "Exchange successful", rack

    def _advance_turn(self) -> None:
        """Advance to the next player's turn."""
        player_ids = sorted(self.players.keys())
        current_idx = player_ids.index(self.current_player_id)
        self.current_player_id = player_ids[(current_idx + 1) % len(player_ids)]
        self.turn_number += 1

    def _calculate_points(self, move_data: List[Tuple[Position, PlacedTile]]) -> int:
        """Calculate points for a move."""
        total_points = 0
        word_multiplier = 1
        
        # Calculate base points with letter multipliers
        for pos, tile in move_data:
            points = LETTER_DISTRIBUTION[self.language]["points"][tile.letter.upper()] if not tile.is_blank else 0
            if pos in self.multipliers:
                multi = self.multipliers[pos]
                if multi == "BL":  # Triple letter score
                    points *= 3
                elif multi == "BW":  # Double letter score
                    points *= 2
                elif multi == "WW":  # Triple word score
                    word_multiplier *= 3
                elif multi == "WL":  # Double word score
                    word_multiplier *= 2
            total_points += points
        
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
                
            word.append(current_tile.letter.upper())
            current_row += 0 if is_horizontal else 1
            current_col += 1 if is_horizontal else 0
        
        return ["".join(word)] if len(word) > 1 else []

    def _validate_word_direction(self, word_positions: List[Tuple[Position, PlacedTile]]) -> Tuple[bool, str]:
        """Validate that all tiles are placed in a single line and are connected."""
        if len(word_positions) <= 1:
            return True, ""
            
        # Determine direction from first two tiles
        is_horizontal = word_positions[0][0].row == word_positions[1][0].row
        reference = word_positions[0][0].row if is_horizontal else word_positions[0][0].col
        
        # Check all tiles are in the same line
        for pos, _ in word_positions[1:]:
            current = pos.row if is_horizontal else pos.col
            if current != reference:
                return False, "All tiles must be placed in a single line"
        
        # Check tiles are connected
        positions = sorted(
            [(pos.col if is_horizontal else pos.row) for pos, _ in word_positions]
        )
        for i in range(len(positions) - 1):
            if positions[i + 1] - positions[i] > 1:
                return False, "All tiles must be connected"
        
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