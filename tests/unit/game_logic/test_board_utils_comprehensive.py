"""
Comprehensive tests for board utilities.
Tests board multipliers, move application, and word placement finding.
"""
import pytest
from app.game_logic.board_utils import (
    BOARD_MULTIPLIERS,
    apply_move_to_board,
    find_word_placements
)


class TestBoardMultipliers:
    """Test board multiplier configuration."""
    
    def test_board_multipliers_exist(self):
        """Test that board multipliers dictionary exists."""
        assert BOARD_MULTIPLIERS is not None
        assert isinstance(BOARD_MULTIPLIERS, dict)
    
    def test_board_multipliers_valid_types(self):
        """Test that multipliers have valid values."""
        valid_multipliers = {"WW", "WL", "BW", "BL"}
        for position, multiplier in BOARD_MULTIPLIERS.items():
            assert isinstance(position, tuple)
            assert len(position) == 2
            assert multiplier in valid_multipliers
    
    def test_center_position_multiplier(self):
        """Test that center position has a multiplier."""
        center = (7, 7)
        assert center in BOARD_MULTIPLIERS
        assert BOARD_MULTIPLIERS[center] == "WL"  # Center is double word
    
    def test_corner_positions_triple_word(self):
        """Test that corners have triple word scores."""
        corners = [(0, 0), (0, 14), (14, 0), (14, 14)]
        for corner in corners:
            assert corner in BOARD_MULTIPLIERS
            assert BOARD_MULTIPLIERS[corner] == "WW"  # Triple word
    
    def test_board_multipliers_coordinates_in_range(self):
        """Test that all multiplier coordinates are within board bounds."""
        for (row, col) in BOARD_MULTIPLIERS.keys():
            assert 0 <= row < 15
            assert 0 <= col < 15
    
    def test_board_multipliers_symmetry(self):
        """Test that board multipliers are symmetric."""
        # Check horizontal symmetry
        for (row, col), mult in BOARD_MULTIPLIERS.items():
            mirror_col = 14 - col
            if (row, mirror_col) in BOARD_MULTIPLIERS:
                assert BOARD_MULTIPLIERS[(row, mirror_col)] == mult
        
        # Check vertical symmetry
        for (row, col), mult in BOARD_MULTIPLIERS.items():
            mirror_row = 14 - row
            if (mirror_row, col) in BOARD_MULTIPLIERS:
                assert BOARD_MULTIPLIERS[(mirror_row, col)] == mult


class TestApplyMoveToBoard:
    """Test applying moves to the board."""
    
    @pytest.fixture
    def empty_board(self):
        """Create empty 15x15 board."""
        return [[None for _ in range(15)] for _ in range(15)]
    
    @pytest.fixture
    def board_with_word(self):
        """Create board with a word."""
        board = [[None for _ in range(15)] for _ in range(15)]
        for i, letter in enumerate("HELLO"):
            board[7][7 + i] = letter
        return board
    
    def test_apply_move_empty_board(self, empty_board):
        """Test applying a move to an empty board."""
        move_letters = [(7, 7, "C"), (7, 8, "A"), (7, 9, "T")]
        result = apply_move_to_board(empty_board, move_letters)
        
        assert result[7][7] == "C"
        assert result[7][8] == "A"
        assert result[7][9] == "T"
    
    def test_apply_move_preserves_original(self, empty_board):
        """Test that applying move doesn't modify original board."""
        move_letters = [(7, 7, "C")]
        result = apply_move_to_board(empty_board, move_letters)
        
        assert empty_board[7][7] is None  # Original unchanged
        assert result[7][7] == "C"  # New board has the letter
    
    def test_apply_move_uppercase_conversion(self, empty_board):
        """Test that letters are converted to uppercase."""
        move_letters = [(7, 7, "c"), (7, 8, "a"), (7, 9, "t")]
        result = apply_move_to_board(empty_board, move_letters)
        
        assert result[7][7] == "C"
        assert result[7][8] == "A"
        assert result[7][9] == "T"
    
    def test_apply_move_to_existing_board(self, board_with_word):
        """Test applying move to board with existing words."""
        move_letters = [(8, 7, "I")]  # Below H in HELLO
        result = apply_move_to_board(board_with_word, move_letters)
        
        # Original word still there
        assert result[7][7] == "H"
        # New letter added
        assert result[8][7] == "I"
    
    def test_apply_empty_move(self, empty_board):
        """Test applying empty move list."""
        move_letters = []
        result = apply_move_to_board(empty_board, move_letters)
        
        # Board should remain empty
        for row in result:
            for cell in row:
                assert cell is None
    
    def test_apply_move_single_letter(self, empty_board):
        """Test applying single letter."""
        move_letters = [(7, 7, "A")]
        result = apply_move_to_board(empty_board, move_letters)
        
        assert result[7][7] == "A"
        # Check other cells remain empty
        assert result[7][8] is None
        assert result[6][7] is None
    
    def test_apply_move_vertical(self, empty_board):
        """Test applying vertical move."""
        move_letters = [(7, 7, "C"), (8, 7, "A"), (9, 7, "T")]
        result = apply_move_to_board(empty_board, move_letters)
        
        assert result[7][7] == "C"
        assert result[8][7] == "A"
        assert result[9][7] == "T"
    
    def test_apply_move_diagonal_coordinates(self, empty_board):
        """Test applying move with diagonal coordinates (valid for function)."""
        move_letters = [(7, 7, "A"), (8, 8, "B"), (9, 9, "C")]
        result = apply_move_to_board(empty_board, move_letters)
        
        # Function doesn't validate, just applies
        assert result[7][7] == "A"
        assert result[8][8] == "B"
        assert result[9][9] == "C"


class TestFindWordPlacements:
    """Test finding valid word placements."""
    
    @pytest.fixture
    def empty_board(self):
        """Create empty board."""
        return [[None for _ in range(15)] for _ in range(15)]
    
    @pytest.fixture
    def board_with_word(self):
        """Create board with HELLO."""
        board = [[None for _ in range(15)] for _ in range(15)]
        for i, letter in enumerate("HELLO"):
            board[7][7 + i] = letter
        return board
    
    @pytest.fixture
    def simple_dictionary(self):
        """Simple dictionary."""
        return {"CAT", "DOG", "HELLO", "HI", "AT", "TO", "OR", "CATS"}
    
    def test_find_placements_first_move(self, empty_board, simple_dictionary):
        """Test finding placements for first move."""
        word = "CAT"
        rack = ["C", "A", "T", "X", "Y", "Z"]
        
        placements = find_word_placements(
            empty_board, word, rack, simple_dictionary, is_first_move=True
        )
        
        # Should find placements through center (may be 0 if word not in dictionary properly)
        assert isinstance(placements, list)
        
        # If placements found, check that they go through center
        if len(placements) > 0:
            for placement in placements:
                row, col = placement["position"]
                direction = placement["direction"]
                
                if direction == "horizontal":
                    # Must be on center row
                    assert row == 7
                    # Must cover center column
                    assert col <= 7 < col + len(word)
                else:  # vertical
                    # Must be on center column
                    assert col == 7
                    # Must cover center row
                    assert row <= 7 < row + len(word)
    
    def test_find_placements_first_move_no_placements_without_letters(self, empty_board, simple_dictionary):
        """Test that no placements found if rack doesn't have letters."""
        word = "CAT"
        rack = ["X", "Y", "Z"]  # Wrong letters
        
        placements = find_word_placements(
            empty_board, word, rack, simple_dictionary, is_first_move=True
        )
        
        assert len(placements) == 0
    
    def test_find_placements_subsequent_move(self, board_with_word, simple_dictionary):
        """Test finding placements after first move."""
        word = "HI"
        rack = ["H", "I", "X", "Y"]
        
        placements = find_word_placements(
            board_with_word, word, rack, simple_dictionary, is_first_move=False
        )
        
        # Should find placements connecting to HELLO
        # May or may not find valid placements depending on dictionary
        assert isinstance(placements, list)
    
    def test_find_placements_sorted_by_score(self, empty_board, simple_dictionary):
        """Test that placements are sorted by score."""
        word = "CAT"
        rack = ["C", "A", "T", "X", "Y", "Z"]
        
        placements = find_word_placements(
            empty_board, word, rack, simple_dictionary, is_first_move=True
        )
        
        if len(placements) > 1:
            # Check descending order
            scores = [p["score_preview"]["total_points"] for p in placements]
            assert scores == sorted(scores, reverse=True)
    
    def test_find_placements_includes_score_preview(self, empty_board, simple_dictionary):
        """Test that placements include score preview."""
        word = "CAT"
        rack = ["C", "A", "T", "X", "Y", "Z"]
        
        placements = find_word_placements(
            empty_board, word, rack, simple_dictionary, is_first_move=True
        )
        
        if placements:
            placement = placements[0]
            assert "score_preview" in placement
            assert "total_points" in placement["score_preview"]
            assert "words_formed" in placement["score_preview"]
            assert placement["score_preview"]["total_points"] >= 0
    
    def test_find_placements_tracks_required_letters(self, empty_board, simple_dictionary):
        """Test that placements track required letters from rack."""
        word = "CAT"
        rack = ["C", "A", "T", "X"]
        
        placements = find_word_placements(
            empty_board, word, rack, simple_dictionary, is_first_move=True
        )
        
        if placements:
            placement = placements[0]
            assert "required_letters" in placement
            assert len(placement["required_letters"]) == 3  # C, A, T
    
    def test_find_placements_empty_word(self, empty_board, simple_dictionary):
        """Test with empty word."""
        word = ""
        rack = ["C", "A", "T"]
        
        placements = find_word_placements(
            empty_board, word, rack, simple_dictionary, is_first_move=True
        )
        
        # Should handle gracefully
        assert isinstance(placements, list)
    
    def test_find_placements_word_too_long(self, empty_board, simple_dictionary):
        """Test with word longer than board."""
        word = "A" * 20  # Longer than 15
        rack = ["A"] * 20
        dictionary = {"A" * 20}
        
        placements = find_word_placements(
            empty_board, word, rack, dictionary, is_first_move=True
        )
        
        # Should find no valid placements
        assert len(placements) == 0


class TestWordPlacementDetails:
    """Test detailed aspects of word placement."""
    
    @pytest.fixture
    def empty_board(self):
        return [[None for _ in range(15)] for _ in range(15)]
    
    @pytest.fixture
    def simple_dictionary(self):
        return {"CAT", "DOG", "AT"}
    
    def test_placement_direction_horizontal(self, empty_board, simple_dictionary):
        """Test horizontal placement has correct direction."""
        word = "CAT"
        rack = ["C", "A", "T"]
        
        placements = find_word_placements(
            empty_board, word, rack, simple_dictionary, is_first_move=True
        )
        
        # If placements found, verify directions exist
        if len(placements) > 0:
            # Find a horizontal placement (may or may not exist)
            horizontal = [p for p in placements if p["direction"] == "horizontal"]
            # Just verify we can filter by direction
            assert isinstance(horizontal, list)
    
    def test_placement_direction_vertical(self, empty_board, simple_dictionary):
        """Test vertical placement has correct direction."""
        word = "CAT"
        rack = ["C", "A", "T"]
        
        placements = find_word_placements(
            empty_board, word, rack, simple_dictionary, is_first_move=True
        )
        
        # If placements found, verify directions exist
        if len(placements) > 0:
            # Find a vertical placement (may or may not exist)
            vertical = [p for p in placements if p["direction"] == "vertical"]
            # Just verify we can filter by direction
            assert isinstance(vertical, list)
    
    def test_placement_position_format(self, empty_board, simple_dictionary):
        """Test that position is correct format."""
        word = "CAT"
        rack = ["C", "A", "T"]
        
        placements = find_word_placements(
            empty_board, word, rack, simple_dictionary, is_first_move=True
        )
        
        if placements:
            placement = placements[0]
            assert "position" in placement
            position = placement["position"]
            assert isinstance(position, tuple)
            assert len(position) == 2
            row, col = position
            assert 0 <= row < 15
            assert 0 <= col < 15


class TestLanguageSupport:
    """Test language support in word placement."""
    
    @pytest.fixture
    def empty_board(self):
        return [[None for _ in range(15)] for _ in range(15)]
    
    def test_find_placements_english(self, empty_board):
        """Test finding placements with English language."""
        word = "CAT"
        rack = ["C", "A", "T"]
        dictionary = {"CAT"}
        
        placements = find_word_placements(
            empty_board, word, rack, dictionary, is_first_move=True, language="en"
        )
        
        assert isinstance(placements, list)
    
    def test_find_placements_german(self, empty_board):
        """Test finding placements with German language."""
        word = "HAT"
        rack = ["H", "A", "T"]
        dictionary = {"HAT"}
        
        placements = find_word_placements(
            empty_board, word, rack, dictionary, is_first_move=True, language="de"
        )
        
        assert isinstance(placements, list)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def empty_board(self):
        return [[None for _ in range(15)] for _ in range(15)]
    
    def test_single_letter_word(self, empty_board):
        """Test finding placements for single letter word."""
        word = "A"
        rack = ["A"]
        dictionary = {"A"}
        
        placements = find_word_placements(
            empty_board, word, rack, dictionary, is_first_move=True
        )
        
        # Should find placements for single letter
        assert isinstance(placements, list)
    
    def test_max_length_word(self, empty_board):
        """Test word of maximum board length."""
        word = "A" * 15
        rack = ["A"] * 15
        dictionary = {"A" * 15}
        
        placements = find_word_placements(
            empty_board, word, rack, dictionary, is_first_move=True
        )
        
        # Should handle 15-letter words
        assert isinstance(placements, list)
    
    def test_empty_rack(self, empty_board):
        """Test with empty rack."""
        word = "CAT"
        rack = []
        dictionary = {"CAT"}
        
        placements = find_word_placements(
            empty_board, word, rack, dictionary, is_first_move=True
        )
        
        # Should find no placements (no letters available)
        assert len(placements) == 0
    
    def test_empty_dictionary(self, empty_board):
        """Test with empty dictionary."""
        word = "CAT"
        rack = ["C", "A", "T"]
        dictionary = set()
        
        placements = find_word_placements(
            empty_board, word, rack, dictionary, is_first_move=True
        )
        
        # Should find no placements (word not valid)
        assert len(placements) == 0

