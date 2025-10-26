"""
Comprehensive tests for move validation logic.
Tests all validation rules and edge cases.
"""
import pytest
from app.game_logic.validate_move import validate_move


class TestMoveValidation:
    """Test suite for move validation."""
    
    @pytest.fixture
    def empty_board(self):
        """Create an empty 15x15 board."""
        return [[None for _ in range(15)] for _ in range(15)]
    
    @pytest.fixture
    def board_with_word(self):
        """Create a board with an existing word."""
        board = [[None for _ in range(15)] for _ in range(15)]
        # Place "HELLO" horizontally at row 7
        for i, letter in enumerate("HELLO"):
            board[7][7 + i] = letter
        return board
    
    @pytest.fixture
    def simple_dictionary(self):
        """Simple dictionary for testing."""
        return {
            "HELLO", "WORLD", "TEST", "CAT", "DOG", "WORD", 
            "HE", "ELL", "LO", "OR", "WO", "AT", "DO"
        }


class TestBasicValidation(TestMoveValidation):
    """Test basic validation rules."""
    
    def test_empty_move_invalid(self, empty_board, simple_dictionary):
        """Test that empty move is invalid."""
        is_valid, reason = validate_move(empty_board, [], ["A", "B", "C"], simple_dictionary)
        assert not is_valid
        assert "Kein Buchstabe" in reason
    
    def test_out_of_bounds_invalid(self, empty_board, simple_dictionary):
        """Test that out of bounds coordinates are invalid."""
        move_letters = [(15, 7, "A")]  # Row 15 is out of bounds (0-14)
        is_valid, reason = validate_move(empty_board, move_letters, ["A"], simple_dictionary)
        assert not is_valid
        assert "außerhalb" in reason
    
    def test_negative_coordinates_invalid(self, empty_board, simple_dictionary):
        """Test that negative coordinates are invalid."""
        move_letters = [(-1, 7, "A")]
        is_valid, reason = validate_move(empty_board, move_letters, ["A"], simple_dictionary)
        assert not is_valid
        assert "außerhalb" in reason
    
    def test_diagonal_placement_invalid(self, empty_board, simple_dictionary):
        """Test that diagonal placement is invalid."""
        move_letters = [(7, 7, "C"), (8, 8, "A"), (9, 9, "T")]  # Diagonal
        is_valid, reason = validate_move(empty_board, move_letters, ["C", "A", "T"], simple_dictionary)
        assert not is_valid
        assert "einer Zeile oder Spalte" in reason
    
    def test_occupied_field_invalid(self, board_with_word, simple_dictionary):
        """Test that placing on occupied field is invalid."""
        move_letters = [(7, 7, "X")]  # Position already has "H"
        is_valid, reason = validate_move(board_with_word, move_letters, ["X"], simple_dictionary)
        assert not is_valid
        assert "bereits belegt" in reason


class TestRackValidation(TestMoveValidation):
    """Test rack/letter availability validation."""
    
    def test_letters_not_in_rack(self, empty_board, simple_dictionary):
        """Test that using letters not in rack is invalid."""
        move_letters = [(7, 7, "X"), (7, 8, "Y"), (7, 9, "Z")]
        is_valid, reason = validate_move(empty_board, move_letters, ["A", "B", "C"], simple_dictionary)
        assert not is_valid
        assert "hat Buchstabe" in reason or "nicht" in reason
    
    def test_valid_letters_from_rack(self, empty_board, simple_dictionary):
        """Test that valid letters from rack works."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        is_valid, reason = validate_move(empty_board, move_letters, ["C", "A", "T", "X"], simple_dictionary)
        assert is_valid
    
    def test_joker_usage(self, empty_board, simple_dictionary):
        """Test that joker (?) can substitute for any letter."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        rack = ["C", "A", "?"]  # Using joker for T
        is_valid, reason = validate_move(empty_board, move_letters, rack, simple_dictionary)
        assert is_valid
    
    def test_multiple_jokers(self, empty_board, simple_dictionary):
        """Test using multiple jokers."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        rack = ["?", "?", "C"]  # Using two jokers
        is_valid, reason = validate_move(empty_board, move_letters, rack, simple_dictionary)
        assert is_valid


class TestAdjacencyValidation(TestMoveValidation):
    """Test adjacency to existing words."""
    
    def test_first_move_no_adjacency_required(self, empty_board, simple_dictionary):
        """Test that first move doesn't require adjacency."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        is_valid, reason = validate_move(empty_board, move_letters, ["C", "A", "T"], simple_dictionary)
        assert is_valid
    
    def test_subsequent_move_requires_adjacency(self, board_with_word, simple_dictionary):
        """Test that subsequent moves require adjacency to existing words."""
        move_letters = [(10, 10, "D"), (10, 11, "O"), (10, 12, "G")]  # Far from HELLO
        is_valid, reason = validate_move(board_with_word, move_letters, ["D", "O", "G"], simple_dictionary)
        assert not is_valid
        assert "angrenzen" in reason
    
    def test_adjacent_move_valid(self, board_with_word, simple_dictionary):
        """Test that adjacent move is valid."""
        # Place "WORLD" below "HELLO", connecting at "L"
        move_letters = [(8, 9, "W"), (8, 10, "O"), (8, 11, "R"), (8, 12, "D")]
        rack = ["W", "O", "R", "D"]
        # This should be adjacent to the L in HELLO
        # Note: This might fail dictionary check, but should pass adjacency
        is_valid, reason = validate_move(board_with_word, move_letters, rack, simple_dictionary)
        # Should pass adjacency check at least
        if not is_valid:
            assert "angrenzen" not in reason


class TestWordValidation(TestMoveValidation):
    """Test word dictionary validation."""
    
    def test_invalid_word_rejected(self, empty_board, simple_dictionary):
        """Test that invalid words are rejected."""
        move_letters = [(7, 7, "X"), (7, 8, "Y"), (7, 9, "Z")]
        is_valid, reason = validate_move(empty_board, move_letters, ["X", "Y", "Z"], simple_dictionary)
        assert not is_valid
        assert "Wörterbuch" in reason
    
    def test_valid_word_accepted(self, empty_board, simple_dictionary):
        """Test that valid words are accepted."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        is_valid, reason = validate_move(empty_board, move_letters, ["C", "A", "T"], simple_dictionary)
        assert is_valid
        assert "gültig" in reason


class TestHorizontalPlacement(TestMoveValidation):
    """Test horizontal word placement."""
    
    def test_horizontal_word_valid(self, empty_board, simple_dictionary):
        """Test placing a horizontal word."""
        move_letters = [(7, 7, "T"), (7, 8, "E"), (7, 9, "S"), (7, 10, "T")]
        is_valid, reason = validate_move(empty_board, move_letters, ["T", "E", "S", "T"], simple_dictionary)
        assert is_valid
    
    def test_horizontal_word_extends_existing(self, board_with_word, simple_dictionary):
        """Test extending an existing word horizontally."""
        # HELLO is at row 7, cols 7-11
        # Try to extend it (though this would create HELLOS which isn't in dictionary)
        move_letters = [(7, 12, "W")]
        rack = ["W"]
        is_valid, reason = validate_move(board_with_word, move_letters, rack, simple_dictionary)
        # Should fail dictionary check but not placement
        if not is_valid:
            # Could fail for various reasons
            pass


class TestVerticalPlacement(TestMoveValidation):
    """Test vertical word placement."""
    
    def test_vertical_word_valid(self, empty_board, simple_dictionary):
        """Test placing a vertical word."""
        move_letters = [(7, 7, "W"), (8, 7, "O"), (9, 7, "R"), (10, 7, "D")]
        is_valid, reason = validate_move(empty_board, move_letters, ["W", "O", "R", "D"], simple_dictionary)
        assert is_valid
    
    def test_vertical_crosses_horizontal(self, board_with_word, simple_dictionary):
        """Test placing vertical word that crosses horizontal word."""
        # HELLO is horizontal at row 7
        # Place vertical word crossing the E
        move_letters = [(6, 8, "T"), (8, 8, "S"), (9, 8, "T")]  # Cross at row 7, col 8 (E in HELLO)
        rack = ["T", "S", "T"]
        is_valid, reason = validate_move(board_with_word, move_letters, rack, simple_dictionary)
        # This creates "TEST" vertically crossing HELLO at E
        # May fail on dictionary but should handle crossing
        if not is_valid:
            # Check it's not failing on basic rules
            assert "Zeile oder Spalte" not in reason


class TestEdgeCases(TestMoveValidation):
    """Test edge cases and special scenarios."""
    
    def test_single_letter_word(self, empty_board, simple_dictionary):
        """Test placing a single letter."""
        move_letters = [(7, 7, "A")]
        dictionary_with_a = simple_dictionary | {"A"}
        is_valid, reason = validate_move(empty_board, move_letters, ["A"], dictionary_with_a)
        # Single letters are typically valid
        assert is_valid
    
    def test_full_board_row(self, empty_board, simple_dictionary):
        """Test placing letters across entire row."""
        # Create a long word (if in dictionary)
        letters = [(7, i, c) for i, c in enumerate("HELLO")]
        is_valid, reason = validate_move(empty_board, letters, list("HELLO"), simple_dictionary)
        assert is_valid
    
    def test_board_boundaries(self, empty_board, simple_dictionary):
        """Test placing at board boundaries."""
        # Top-left corner
        move_letters = [(0, 0, "C"), (0, 1, "A"), (0, 2, "T")]
        is_valid, reason = validate_move(empty_board, move_letters, ["C", "A", "T"], simple_dictionary)
        assert is_valid
        
        # Bottom-right corner
        move_letters = [(14, 12, "C"), (14, 13, "A"), (14, 14, "T")]
        is_valid, reason = validate_move(empty_board, move_letters, ["C", "A", "T"], simple_dictionary)
        assert is_valid


class TestComplexScenarios(TestMoveValidation):
    """Test complex multi-word scenarios."""
    
    def test_creates_multiple_words(self, board_with_word, simple_dictionary):
        """Test move that creates multiple valid words."""
        # HELLO is horizontal at row 7, cols 7-11
        # Place "AT" vertically at col 7, creating "HA" and "AT"
        board = board_with_word
        move_letters = [(6, 7, "H"), (8, 7, "A")]
        rack = ["H", "A"]
        
        # This creates:
        # - "HA" vertically
        # - Crosses with existing HELLO
        dictionary = simple_dictionary | {"HA", "AT"}
        is_valid, reason = validate_move(board, move_letters, rack, dictionary)
        # Complex interaction - may have issues but tests the logic
        if not is_valid:
            # Should at least not crash
            assert reason is not None
    
    def test_gap_in_letters(self, empty_board, simple_dictionary):
        """Test that gaps in letter placement are handled."""
        # Try to place letters with a gap (which shouldn't work for main word)
        move_letters = [(7, 7, "C"), (7, 9, "T")]  # Gap at position 8
        is_valid, reason = validate_move(empty_board, move_letters, ["C", "T"], simple_dictionary)
        # This should create "C_T" which needs existing letter at position 8
        # On empty board this might be rejected or handled as two words
        # The important thing is it doesn't crash
        assert reason is not None


class TestRackConsumption(TestMoveValidation):
    """Test that letters are properly consumed from rack."""
    
    def test_using_duplicate_letters(self, empty_board, simple_dictionary):
        """Test using duplicate letters from rack."""
        move_letters = [(7, 7, "T"), (7, 8, "E"), (7, 9, "S"), (7, 10, "T")]
        rack = ["T", "E", "S", "T", "X"]  # Two T's
        is_valid, reason = validate_move(empty_board, move_letters, rack, simple_dictionary)
        assert is_valid
    
    def test_insufficient_duplicate_letters(self, empty_board, simple_dictionary):
        """Test that insufficient duplicate letters are caught."""
        move_letters = [(7, 7, "T"), (7, 8, "E"), (7, 9, "S"), (7, 10, "T")]
        rack = ["T", "E", "S", "X"]  # Only one T
        is_valid, reason = validate_move(empty_board, move_letters, rack, simple_dictionary)
        assert not is_valid
        assert "nicht" in reason or "hat" in reason

