"""
Comprehensive tests for game_state.py

Covers:
- GamePhase and MoveType enums
- Position and PlacedTile dataclasses
- GameState initialization
- Player management
- Game lifecycle (start, moves, end)
- Scoring and turn management
- Word validation
- Edge cases and error handling
"""

import pytest
from app.game_logic.game_state import (
    GameState, GamePhase, MoveType, Position, PlacedTile,
    LETTER_DISTRIBUTION
)


# ============================================================================
# ENUMS AND DATACLASSES
# ============================================================================

class TestEnumsAndDataclasses:
    """Test enums and dataclasses."""
    
    def test_game_phase_values(self):
        """Test GamePhase enum values."""
        assert GamePhase.NOT_STARTED.value == "not_started"
        assert GamePhase.IN_PROGRESS.value == "in_progress"
        assert GamePhase.COMPLETED.value == "completed"
    
    def test_move_type_values(self):
        """Test MoveType enum values."""
        assert MoveType.PLACE.value == "PLACE"
        assert MoveType.EXCHANGE.value == "EXCHANGE"
        assert MoveType.PASS.value == "PASS"
    
    def test_position_creation(self):
        """Test Position dataclass creation."""
        pos = Position(row=7, col=7)
        assert pos.row == 7
        assert pos.col == 7
    
    def test_position_equality(self):
        """Test Position equality comparison."""
        pos1 = Position(row=7, col=7)
        pos2 = Position(row=7, col=7)
        pos3 = Position(row=7, col=8)
        
        assert pos1 == pos2
        assert pos1 != pos3
    
    def test_position_hash(self):
        """Test Position hashing for set/dict usage."""
        pos1 = Position(row=7, col=7)
        pos2 = Position(row=7, col=7)
        pos3 = Position(row=7, col=8)
        
        assert hash(pos1) == hash(pos2)
        assert hash(pos1) != hash(pos3)
        
        # Can be used in sets
        positions = {pos1, pos2, pos3}
        assert len(positions) == 2  # pos1 and pos2 are same
    
    def test_placed_tile_regular(self):
        """Test PlacedTile for regular letters."""
        tile = PlacedTile(letter="A", language="en")
        
        assert tile.letter == "A"
        assert tile.is_blank is False
        assert tile.points == 1  # A is worth 1 point in English
        assert tile.tile_id is not None
    
    def test_placed_tile_blank(self):
        """Test PlacedTile for blank tiles."""
        tile = PlacedTile(letter="A", is_blank=True, language="en")
        
        assert tile.letter == "A"
        assert tile.is_blank is True
        assert tile.points == 0  # Blank tiles worth 0
        assert tile.tile_id is not None
    
    def test_placed_tile_high_value(self):
        """Test PlacedTile for high-value letters."""
        tile_q = PlacedTile(letter="Q", language="en")
        tile_z = PlacedTile(letter="Z", language="en")
        
        assert tile_q.points == 10  # Q is worth 10 in English
        assert tile_z.points == 10  # Z is worth 10 in English
    
    def test_placed_tile_custom_id(self):
        """Test PlacedTile with custom tile_id."""
        tile = PlacedTile(letter="X", tile_id="custom-123", language="en")
        
        assert tile.tile_id == "custom-123"
        assert tile.points == 8  # X is worth 8 in English


# ============================================================================
# GAME STATE INITIALIZATION
# ============================================================================

class TestGameStateInitialization:
    """Test GameState initialization."""
    
    def test_default_initialization(self):
        """Test GameState initialization with defaults."""
        game = GameState()
        
        assert game.phase == GamePhase.NOT_STARTED
        assert game.language == "en"
        assert len(game.board) == 15
        assert len(game.board[0]) == 15
        assert all(cell is None for row in game.board for cell in row)
        assert game.players == {}
        assert game.scores == {}
        assert game.current_player_id is None
        assert game.turn_number == 0
        assert game.consecutive_passes == 0
        assert game.center_used is False
        assert len(game.letter_bag) > 0  # Should have letters
    
    def test_language_initialization(self):
        """Test GameState with different languages."""
        game_en = GameState(language="en")
        game_de = GameState(language="de")
        
        assert game_en.language == "en"
        assert game_de.language == "de"
        assert len(game_en.letter_bag) > 0
        assert len(game_de.letter_bag) > 0
    
    def test_short_game_initialization(self):
        """Test GameState with short_game flag."""
        game_normal = GameState(short_game=False)
        game_short = GameState(short_game=True)
        
        # Short game should have fewer letters
        assert len(game_short.letter_bag) < len(game_normal.letter_bag)


# ============================================================================
# PLAYER MANAGEMENT
# ============================================================================

class TestPlayerManagement:
    """Test player management functions."""
    
    def test_add_player(self):
        """Test adding a player to the game."""
        game = GameState()
        
        rack = game.add_player(1)
        
        assert 1 in game.players
        assert game.players[1] == rack
        assert len(rack) == 7  # Initial rack is 7 letters
        assert 1 in game.scores
        assert game.scores[1] == 0
    
    def test_add_multiple_players(self):
        """Test adding multiple players."""
        game = GameState()
        
        rack1 = game.add_player(1)
        rack2 = game.add_player(2)
        
        assert len(game.players) == 2
        assert rack1 != rack2  # Different racks
        assert len(rack1) == 7
        assert len(rack2) == 7
    
    def test_add_duplicate_player(self):
        """Test adding same player twice raises error."""
        game = GameState()
        game.add_player(1)
        
        with pytest.raises(ValueError, match="Player already in game"):
            game.add_player(1)
    
    def test_start_game_success(self):
        """Test starting a game successfully."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        
        game.start_game(1)
        
        assert game.phase == GamePhase.IN_PROGRESS
        assert game.current_player_id == 1
    
    def test_start_game_not_enough_players(self):
        """Test starting game with < 2 players fails."""
        game = GameState()
        game.add_player(1)
        
        with pytest.raises(ValueError, match="Need at least 2 players"):
            game.start_game(1)
    
    def test_start_game_invalid_first_player(self):
        """Test starting game with non-existent player fails."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        
        with pytest.raises(ValueError, match="First player not in game"):
            game.start_game(99)


# ============================================================================
# TURN MANAGEMENT
# ============================================================================

class TestTurnManagement:
    """Test turn management and rotation."""
    
    def test_advance_turn_two_players(self):
        """Test turn rotation with 2 players."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        assert game.current_player_id == 1
        assert game.turn_number == 0
        
        game._advance_turn()
        
        assert game.current_player_id == 2
        assert game.turn_number == 1
        
        game._advance_turn()
        
        assert game.current_player_id == 1
        assert game.turn_number == 2
    
    def test_advance_turn_three_players(self):
        """Test turn rotation with 3 players."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.add_player(3)
        game.start_game(1)
        
        assert game.current_player_id == 1
        
        game._advance_turn()
        assert game.current_player_id == 2
        
        game._advance_turn()
        assert game.current_player_id == 3
        
        game._advance_turn()
        assert game.current_player_id == 1  # Back to first


# ============================================================================
# PASS MOVES
# ============================================================================

class TestPassMoves:
    """Test pass move functionality."""
    
    def test_pass_move_success(self):
        """Test successful pass move."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        dictionary = set()  # Empty dictionary for pass
        success, msg, points, words = game.make_move(
            1, MoveType.PASS, [], dictionary
        )
        
        assert success is True
        assert "passed" in msg.lower()
        assert points == 0
        assert words == []
        assert game.consecutive_passes == 1
        assert game.current_player_id == 2  # Turn advanced
    
    def test_multiple_passes(self):
        """Test multiple consecutive passes."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        dictionary = set()
        
        # Player 1 passes
        game.make_move(1, MoveType.PASS, [], dictionary)
        assert game.consecutive_passes == 1
        
        # Player 2 passes
        game.make_move(2, MoveType.PASS, [], dictionary)
        assert game.consecutive_passes == 2
    
    def test_pass_wrong_turn(self):
        """Test pass on wrong turn fails."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        dictionary = set()
        success, msg, points, words = game.make_move(
            2, MoveType.PASS, [], dictionary  # Player 2, but it's player 1's turn
        )
        
        assert success is False
        assert "not your turn" in msg.lower()
        assert points == 0


# ============================================================================
# GAME STATE VALIDATION
# ============================================================================

class TestGameStateValidation:
    """Test game state validation for moves."""
    
    def test_move_before_game_start(self):
        """Test move before game starts fails."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        # Don't start game
        
        dictionary = set()
        success, msg, points, words = game.make_move(
            1, MoveType.PASS, [], dictionary
        )
        
        assert success is False
        assert "not started" in msg.lower()
    
    def test_move_after_game_end(self):
        """Test move after game ends fails."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        # Force game to end
        game.phase = GamePhase.COMPLETED
        
        dictionary = set()
        success, msg, points, words = game.make_move(
            1, MoveType.PASS, [], dictionary
        )
        
        assert success is False
        assert "ended" in msg.lower() or "completed" in msg.lower()


# ============================================================================
# WORD PLACEMENT VALIDATION
# ============================================================================

class TestWordPlacement:
    """Test word placement validation."""
    
    def test_first_move_center_required(self):
        """Test first move must use center square."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        # Set rack
        game.players[1] = "CATTEST"
        
        # Try to place word NOT using center
        move_data = [
            (Position(0, 0), PlacedTile("C", language="en")),
            (Position(0, 1), PlacedTile("A", language="en")),
            (Position(0, 2), PlacedTile("T", language="en")),
        ]
        
        dictionary = {"CAT"}
        success, msg, words = game.validate_word_placement(move_data, dictionary)
        
        assert success is False
        assert "center" in msg.lower()
    
    def test_first_move_center_success(self):
        """Test first move using center succeeds."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        # Set rack
        game.players[1] = "CATTEST"
        
        # Place word using center (7, 7)
        move_data = [
            (Position(7, 7), PlacedTile("C", language="en")),
            (Position(7, 8), PlacedTile("A", language="en")),
            (Position(7, 9), PlacedTile("T", language="en")),
        ]
        
        dictionary = {"CAT"}
        success, msg, words = game.validate_word_placement(move_data, dictionary)
        
        assert success is True
        assert len(words) == 1
        assert words[0] == "CAT"
    
    def test_out_of_bounds_placement(self):
        """Test placing tiles out of bounds fails."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        game.center_used = True  # Skip center check to test bounds
        
        # Try to place tile outside board
        move_data = [
            (Position(15, 15), PlacedTile("X", language="en")),  # Out of bounds
        ]
        
        dictionary = {"X"}
        success, msg, words = game.validate_word_placement(move_data, dictionary)
        
        assert success is False
        assert "outside" in msg.lower() or "boundaries" in msg.lower()
    
    def test_overlapping_tile_placement(self):
        """Test placing tile on existing tile fails."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        # Place a tile on the board
        game.board[7][7] = PlacedTile("X", language="en")
        game.center_used = True
        
        # Try to place another tile in same position
        move_data = [
            (Position(7, 7), PlacedTile("Y", language="en")),
        ]
        
        dictionary = {"Y"}
        success, msg, words = game.validate_word_placement(move_data, dictionary)
        
        assert success is False
        assert "already" in msg.lower()
    
    def test_invalid_word_in_dictionary(self):
        """Test placing invalid word fails."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        # Place word that's NOT in dictionary
        move_data = [
            (Position(7, 7), PlacedTile("X", language="en")),
            (Position(7, 8), PlacedTile("Y", language="en")),
            (Position(7, 9), PlacedTile("Z", language="en")),
        ]
        
        dictionary = {"CAT", "DOG"}  # XYZ not in dictionary
        success, msg, words = game.validate_word_placement(move_data, dictionary)
        
        assert success is False
        assert "not a valid word" in msg.lower() or "invalid" in msg.lower()


# ============================================================================
# RACK MANAGEMENT
# ============================================================================

class TestRackManagement:
    """Test rack replenishment and management."""
    
    def test_replenish_rack_normal(self):
        """Test rack replenishment after move."""
        game = GameState()
        game.add_player(1)
        
        # Set rack to known state
        game.players[1] = "ABCDEFG"
        initial_bag_size = len(game.letter_bag)
        
        # Remove 3 letters
        game._replenish_rack(1, ["A", "B", "C"])
        
        # Rack should be refilled to 7
        assert len(game.players[1]) == 7
        assert "A" not in game.players[1]
        assert "B" not in game.players[1]
        assert "C" not in game.players[1]
        
        # Bag should have 3 fewer letters
        assert len(game.letter_bag) == initial_bag_size - 3
    
    def test_replenish_rack_empty_bag(self):
        """Test rack replenishment when bag is empty."""
        game = GameState()
        game.add_player(1)
        
        # Empty the bag
        game.letter_bag = ""
        game.players[1] = "ABCDEFG"
        
        # Remove letters
        game._replenish_rack(1, ["A", "B", "C"])
        
        # Rack should have 4 letters (no replenishment)
        assert len(game.players[1]) == 4
        assert game.players[1] == "DEFG"


# ============================================================================
# SCORING
# ============================================================================

class TestScoring:
    """Test scoring calculations."""
    
    def test_basic_word_scoring(self):
        """Test basic word scoring without multipliers."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        game.center_used = True  # Skip first move bonus
        
        # Place CAT (C=3, A=1, T=1 = 5 points)
        move_data = [
            (Position(0, 0), PlacedTile("C", language="en")),
            (Position(0, 1), PlacedTile("A", language="en")),
            (Position(0, 2), PlacedTile("T", language="en")),
        ]
        
        points = game._calculate_points(move_data)
        assert points >= 5  # At least base points
    
    def test_seven_tile_bonus(self):
        """Test 50-point bonus for using all 7 tiles."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        game.center_used = True
        
        # Place 7 tiles
        move_data = [
            (Position(0, i), PlacedTile("A", language="en"))
            for i in range(7)
        ]
        
        points = game._calculate_points(move_data)
        # Should include 50 point bonus
        assert points >= 50


# ============================================================================
# GAME END CONDITIONS
# ============================================================================

class TestGameEndConditions:
    """Test game end conditions."""
    
    def test_game_not_ended_initial(self):
        """Test game doesn't end initially."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        ended, details = game.check_game_end()
        
        assert ended is False
        assert details is None
    
    def test_game_ends_empty_rack(self):
        """Test game ends when player empties rack."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        # Empty player 1's rack
        game.players[1] = ""
        game.scores[1] = 100
        game.scores[2] = 50
        
        ended, details = game.check_game_end()
        
        assert ended is True
        assert details is not None
        assert details["winner_id"] in [1, 2]
        assert details["end_reason"] == "empty_rack"
    
    def test_game_ends_all_players_pass(self):
        """Test game ends when all players pass 3 times."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        # Simulate 6 consecutive passes (3 per player)
        game.consecutive_passes = 6
        game.scores[1] = 100
        game.scores[2] = 80
        
        ended, details = game.check_game_end()
        
        assert ended is True
        assert details is not None
        assert details["winner_id"] == 1  # Player 1 has higher score
        assert details["end_reason"] == "all_players_passed_three_times"
    
    def test_game_end_phase_change(self):
        """Test phase changes to COMPLETED on game end."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        # Empty player 1's rack
        game.players[1] = ""
        game.scores[1] = 100
        game.scores[2] = 50
        
        game.check_game_end()
        
        assert game.phase == GamePhase.COMPLETED


# ============================================================================
# HELPER METHODS
# ============================================================================

class TestHelperMethods:
    """Test helper methods."""
    
    def test_is_connected_to_existing_true(self):
        """Test connection detection when tiles are adjacent."""
        game = GameState()
        
        # Place a tile on the board
        game.board[7][7] = PlacedTile("X", language="en")
        
        # New tiles adjacent to existing
        move_data = [
            (Position(7, 8), PlacedTile("Y", language="en")),
        ]
        
        is_connected = game._is_connected_to_existing(move_data)
        assert is_connected is True
    
    def test_is_connected_to_existing_false(self):
        """Test connection detection when tiles are isolated."""
        game = GameState()
        
        # Place a tile on the board
        game.board[0][0] = PlacedTile("X", language="en")
        
        # New tiles NOT adjacent
        move_data = [
            (Position(10, 10), PlacedTile("Y", language="en")),
        ]
        
        is_connected = game._is_connected_to_existing(move_data)
        assert is_connected is False
    
    def test_validate_word_direction_horizontal(self):
        """Test word direction validation for horizontal."""
        game = GameState()
        
        # Horizontal word
        move_data = [
            (Position(7, 7), PlacedTile("C", language="en")),
            (Position(7, 8), PlacedTile("A", language="en")),
            (Position(7, 9), PlacedTile("T", language="en")),
        ]
        
        valid, msg = game._validate_word_direction(move_data)
        assert valid is True
    
    def test_validate_word_direction_vertical(self):
        """Test word direction validation for vertical."""
        game = GameState()
        
        # Vertical word
        move_data = [
            (Position(5, 7), PlacedTile("C", language="en")),
            (Position(6, 7), PlacedTile("A", language="en")),
            (Position(7, 7), PlacedTile("T", language="en")),
        ]
        
        valid, msg = game._validate_word_direction(move_data)
        assert valid is True
    
    def test_validate_word_direction_diagonal(self):
        """Test word direction validation fails for diagonal."""
        game = GameState()
        
        # Diagonal placement (invalid)
        move_data = [
            (Position(7, 7), PlacedTile("C", language="en")),
            (Position(8, 8), PlacedTile("A", language="en")),
            (Position(9, 9), PlacedTile("T", language="en")),
        ]
        
        valid, msg = game._validate_word_direction(move_data)
        assert valid is False
        assert "row" in msg.lower() or "column" in msg.lower()


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_move_data(self):
        """Test validation with empty move data."""
        game = GameState()
        
        dictionary = {"CAT"}
        success, msg, words = game.validate_word_placement([], dictionary)
        
        assert success is False
        assert "no tiles" in msg.lower() or "at least one" in msg.lower()
    
    def test_single_letter_placement(self):
        """Test single letter placement."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        # Can't place single letter as first move
        move_data = [
            (Position(7, 7), PlacedTile("A", language="en")),
        ]
        
        dictionary = {"A"}
        success, msg, words = game.validate_word_placement(move_data, dictionary)
        
        # First move needs to use center and form valid word
        # Single letter won't form a word, so should fail
        assert success is False
    
    def test_max_board_size(self):
        """Test board boundaries at maximum coordinates."""
        game = GameState()
        
        # Test corner positions
        assert game.board[0][0] is None
        assert game.board[0][14] is None
        assert game.board[14][0] is None
        assert game.board[14][14] is None
    
    def test_skip_turn_validation(self):
        """Test skip_turn_validation parameter."""
        game = GameState()
        game.add_player(1)
        game.add_player(2)
        game.start_game(1)
        
        dictionary = set()
        # Player 2 makes move on player 1's turn with skip_turn_validation
        success, msg, points, words = game.make_move(
            2, MoveType.PASS, [], dictionary, skip_turn_validation=True
        )
        
        assert success is True  # Should succeed with validation skipped
        assert game.current_player_id == 2  # Turn advanced (1 -> 2)
    
    def test_pattern_validation_caching(self):
        """Test that pattern validation uses caching."""
        game = GameState()
        dictionary = {"CAT", "DOG", "BIRD"}
        
        # First call - should cache
        result1 = game._is_valid_word_pattern("C?T", dictionary)
        
        # Second call - should use cache
        result2 = game._is_valid_word_pattern("C?T", dictionary)
        
        assert result1 == result2
        assert "C?T" in game._pattern_cache
    
    def test_clear_validation_caches(self):
        """Test clearing validation caches."""
        game = GameState()
        dictionary = {"CAT"}
        
        # Populate caches
        game._is_valid_word_pattern("C?T", dictionary)
        assert len(game._pattern_cache) > 0
        
        # Clear caches
        game._clear_validation_caches()
        
        assert len(game._pattern_cache) == 0
        assert len(game._compiled_patterns) == 0
        assert game._dictionary_by_length is None

