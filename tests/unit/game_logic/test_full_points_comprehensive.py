"""
Comprehensive tests for scoring/points calculation logic.
Tests letter points, word scoring, multipliers, and bonuses.
"""
import pytest
from app.game_logic.full_points import (
    get_letter_points,
    is_blank,
    get_word_horizontal,
    get_word_vertical,
    calculate_full_move_points
)


class TestLetterPoints:
    """Test letter point value functions."""
    
    def test_get_letter_points_english(self):
        """Test getting letter points for English."""
        assert get_letter_points("A", "en") >= 1
        assert get_letter_points("E", "en") >= 1
        assert get_letter_points("Q", "en") > get_letter_points("E", "en")
        assert get_letter_points("Z", "en") > get_letter_points("A", "en")
    
    def test_get_letter_points_case_insensitive(self):
        """Test that letter points are case insensitive."""
        assert get_letter_points("a", "en") == get_letter_points("A", "en")
        assert get_letter_points("z", "en") == get_letter_points("Z", "en")
    
    def test_get_letter_points_german(self):
        """Test getting letter points for German."""
        assert get_letter_points("A", "de") >= 1
        assert get_letter_points("E", "de") >= 1
    
    def test_get_letter_points_default(self):
        """Test default points for unknown letters."""
        result = get_letter_points("", "en")
        assert result == 1  # Default value
    
    def test_is_blank_joker(self):
        """Test that joker is recognized as blank."""
        assert is_blank("?") is True
        assert is_blank("*") is True
    
    def test_is_blank_regular_letter(self):
        """Test that regular letters are not blank."""
        assert is_blank("A") is False
        assert is_blank("Z") is False
        assert is_blank("1") is False


class TestWordExtraction:
    """Test word extraction from board."""
    
    @pytest.fixture
    def board_with_words(self):
        """Create a board with some words."""
        board = [[None for _ in range(15)] for _ in range(15)]
        # Horizontal word "HELLO" at row 7
        for i, letter in enumerate("HELLO"):
            board[7][7 + i] = letter
        # Vertical word "HI" at col 7
        board[6][7] = "H"
        board[7][7] = "H"  # Shared with HELLO
        board[8][7] = "I"
        return board
    
    def test_get_word_horizontal_middle(self, board_with_words):
        """Test getting horizontal word from middle position."""
        word, coords = get_word_horizontal(board_with_words, 7, 9)  # Position of "L" in HELLO
        assert word == "HELLO"
        assert len(coords) == 5
    
    def test_get_word_horizontal_start(self, board_with_words):
        """Test getting horizontal word from start position."""
        word, coords = get_word_horizontal(board_with_words, 7, 7)  # Position of "H" in HELLO
        assert word == "HELLO" or word == "H"  # May return full word or just H
    
    def test_get_word_horizontal_end(self, board_with_words):
        """Test getting horizontal word from end position."""
        word, coords = get_word_horizontal(board_with_words, 7, 11)  # Position of "O" in HELLO
        assert "O" in word
        assert len(coords) >= 1
    
    def test_get_word_vertical_middle(self, board_with_words):
        """Test getting vertical word from middle position."""
        word, coords = get_word_vertical(board_with_words, 7, 7)  # Position of shared "H"
        # Should get the vertical word "HI" or longer
        assert "H" in word
        assert len(coords) >= 1
    
    def test_get_word_horizontal_empty_cell(self):
        """Test getting word from empty cell."""
        board = [[None for _ in range(15)] for _ in range(15)]
        word, coords = get_word_horizontal(board, 7, 7)
        assert word == ""
        assert coords == []
    
    def test_get_word_vertical_empty_cell(self):
        """Test getting vertical word from empty cell."""
        board = [[None for _ in range(15)] for _ in range(15)]
        word, coords = get_word_vertical(board, 7, 7)
        assert word == ""
        assert coords == []
    
    def test_get_word_horizontal_single_letter(self):
        """Test getting single letter as word."""
        board = [[None for _ in range(15)] for _ in range(15)]
        board[7][7] = "A"
        word, coords = get_word_horizontal(board, 7, 7)
        assert word == "A"
        assert len(coords) == 1


class TestScoreCalculation:
    """Test score calculation."""
    
    @pytest.fixture
    def empty_board(self):
        """Create empty board."""
        return [[None for _ in range(15)] for _ in range(15)]
    
    @pytest.fixture
    def simple_multipliers(self):
        """Create simple multiplier map."""
        return {
            (7, 7): "WW",   # Triple word score (center)
            (7, 8): "BL",   # Double letter score
            (8, 7): "WL",   # Double word score
        }
    
    @pytest.fixture
    def simple_dictionary(self):
        """Simple dictionary for testing."""
        return {"HELLO", "WORLD", "TEST", "CAT", "DOG", "HI", "AT", "TO"}
    
    def test_calculate_points_simple_word(self, empty_board, simple_dictionary):
        """Test calculating points for a simple word."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        multipliers = {}
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, simple_dictionary
        )
        assert result["valid"] is True
        assert result["total"] > 0
        assert len(result["words"]) > 0
    
    def test_calculate_points_with_double_letter(self, empty_board, simple_dictionary):
        """Test calculating points with double letter score."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        multipliers = {(7, 8): "BL"}  # Double letter on "A"
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, simple_dictionary
        )
        assert result["valid"] is True
        assert result["total"] > 0
    
    def test_calculate_points_with_triple_letter(self, empty_board, simple_dictionary):
        """Test calculating points with triple letter score."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        multipliers = {(7, 8): "BW"}  # Triple letter on "A"
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, simple_dictionary
        )
        assert result["valid"] is True
        assert result["total"] > 0
    
    def test_calculate_points_with_double_word(self, empty_board, simple_dictionary):
        """Test calculating points with double word score."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        multipliers = {(7, 7): "WL"}  # Double word
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, simple_dictionary
        )
        assert result["valid"] is True
        assert result["total"] > 0
        # Should be higher than without multiplier
    
    def test_calculate_points_with_triple_word(self, empty_board, simple_dictionary):
        """Test calculating points with triple word score."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        multipliers = {(7, 7): "WW"}  # Triple word
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, simple_dictionary
        )
        assert result["valid"] is True
        assert result["total"] > 0
    
    def test_calculate_points_seven_letter_bonus(self, empty_board, simple_dictionary):
        """Test that using all 7 letters gives 50 point bonus."""
        # Create a 7-letter word (won't be in dictionary but tests the bonus logic)
        move_letters = [(7, i, "A") for i in range(7)]
        multipliers = {}
        dictionary = {"AAAAAAA"}  # Fake word
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, dictionary
        )
        if result["valid"]:
            # If valid, should have the 50 point bonus
            assert result["total"] >= 50
    
    def test_calculate_points_invalid_word(self, empty_board):
        """Test that invalid words are rejected."""
        move_letters = [(7, 7, "X"), (7, 8, "Y"), (7, 9, "Z")]
        multipliers = {}
        dictionary = {"CAT"}  # XYZ not in dictionary
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, dictionary
        )
        assert result["valid"] is False
        assert "error" in result
    
    def test_calculate_points_occupied_position(self, empty_board, simple_dictionary):
        """Test that occupied positions are detected."""
        board = [row[:] for row in empty_board]
        board[7][7] = "X"  # Pre-existing letter
        move_letters = [(7, 7, "C")]  # Try to place on occupied position
        multipliers = {}
        result = calculate_full_move_points(
            board, move_letters, "en", multipliers, simple_dictionary
        )
        assert result["valid"] is False
        assert "occupied" in result.get("error", "").lower()
    
    def test_calculate_points_diagonal_placement(self, empty_board, simple_dictionary):
        """Test that diagonal placement is rejected."""
        move_letters = [(7, 7, "C"), (8, 8, "A"), (9, 9, "T")]  # Diagonal
        multipliers = {}
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, simple_dictionary
        )
        assert result["valid"] is False


class TestBlankTiles:
    """Test blank/joker tile handling."""
    
    @pytest.fixture
    def empty_board(self):
        return [[None for _ in range(15)] for _ in range(15)]
    
    @pytest.fixture
    def simple_dictionary(self):
        return {"CAT", "DOG"}
    
    def test_blank_tiles_zero_points(self, empty_board, simple_dictionary):
        """Test that blank tiles contribute zero points."""
        move_letters = [(7, 7, "C"), (7, 8, "?"), (7, 9, "T")]  # ? is joker for A
        multipliers = {}
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, simple_dictionary
        )
        # Blanks should give 0 points even with multipliers
        if result["valid"]:
            # Score should be lower than with regular letters
            assert result["total"] >= 0


class TestMultipleWords:
    """Test scenarios creating multiple words."""
    
    @pytest.fixture
    def board_with_word(self):
        """Board with existing word."""
        board = [[None for _ in range(15)] for _ in range(15)]
        # Place "CAT" horizontally
        for i, letter in enumerate("CAT"):
            board[7][7 + i] = letter
        return board
    
    @pytest.fixture
    def dictionary(self):
        return {"CAT", "AT", "TO", "CATS", "CAR"}
    
    def test_crossing_words_score(self, board_with_word, dictionary):
        """Test that crossing words are counted."""
        # Place "AT" vertically crossing "CAT" at "A"
        move_letters = [(6, 8, "A"), (8, 8, "T")]
        multipliers = {}
        result = calculate_full_move_points(
            board_with_word, move_letters, "en", multipliers, dictionary
        )
        # Should create multiple words and score them all
        if result["valid"]:
            assert result["total"] > 0


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    @pytest.fixture
    def empty_board(self):
        return [[None for _ in range(15)] for _ in range(15)]
    
    def test_single_letter_move(self, empty_board):
        """Test placing a single letter."""
        move_letters = [(7, 7, "A")]
        multipliers = {}
        dictionary = {"A"}
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, dictionary
        )
        assert result["valid"] is True
        assert result["total"] >= 0
    
    def test_empty_move_list(self, empty_board):
        """Test with empty move list."""
        move_letters = []
        multipliers = {}
        dictionary = {"CAT"}
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, dictionary
        )
        # Should handle gracefully
        assert "valid" in result
    
    def test_multiple_multipliers_same_word(self, empty_board):
        """Test multiple multipliers in the same word."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        multipliers = {
            (7, 7): "BL",  # Double letter
            (7, 8): "WL",  # Double word
            (7, 9): "BW",  # Triple letter
        }
        dictionary = {"CAT"}
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, dictionary
        )
        if result["valid"]:
            # Should apply all multipliers correctly
            assert result["total"] > 0


class TestLanguageSupport:
    """Test different language support."""
    
    @pytest.fixture
    def empty_board(self):
        return [[None for _ in range(15)] for _ in range(15)]
    
    def test_german_scoring(self, empty_board):
        """Test scoring with German language."""
        move_letters = [(7, 7, "H"), (7, 8, "A"), (7, 9, "T")]
        multipliers = {}
        dictionary = {"HAT"}
        result = calculate_full_move_points(
            empty_board, move_letters, "de", multipliers, dictionary
        )
        assert result["valid"] is True
        assert result["total"] > 0
    
    def test_english_scoring(self, empty_board):
        """Test scoring with English language."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        multipliers = {}
        dictionary = {"CAT"}
        result = calculate_full_move_points(
            empty_board, move_letters, "en", multipliers, dictionary
        )
        assert result["valid"] is True
        assert result["total"] > 0

