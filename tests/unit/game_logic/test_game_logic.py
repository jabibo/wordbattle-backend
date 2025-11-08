from app.game_logic.validate_move import validate_move
from app.game_logic.full_points import calculate_full_move_points, LETTER_POINTS
from app.game_logic.board_utils import apply_move_to_board, find_word_placements, BOARD_MULTIPLIERS
from app.models.game import GameStatus

def test_validate_move_out_of_bounds():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Test move with coordinates outside the board bounds
    # First check if coordinates are valid before accessing the board
    move_letters = [(14, 14, "X")]  # Valid coordinates at edge
    player_rack = ["X"]
    dictionary = set(["X"])
    
    is_valid, reason = validate_move(board, move_letters, player_rack, dictionary)
    assert is_valid
    
    # Now test with invalid coordinates
    move_letters = [(15, 7, "X")]  # Invalid row
    is_valid, _ = validate_move(board, move_letters, player_rack, dictionary)
    assert not is_valid

def test_validate_move_letters_not_in_rack():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Test move with letters not in player's rack
    move_letters = [(7, 7, "Z"), (7, 8, "Y")]
    player_rack = ["A", "B", "C"]
    dictionary = set(["ZY"])
    
    is_valid, reason = validate_move(board, move_letters, player_rack, dictionary)
    assert not is_valid
    assert "nicht" in reason

def test_calculate_points_with_multipliers():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Place a word using letter and word multipliers
    move_letters = [(7, 7, "T"), (7, 8, "E"), (7, 9, "S"), (7, 10, "T")]  # TEST
    dictionary = set(["TEST"])
    
    result = calculate_full_move_points(board, move_letters, LETTER_POINTS, BOARD_MULTIPLIERS, dictionary)
    assert result["valid"]
    assert result["total"] > 0
    assert "TEST" in [word for word, _ in result["words"]]

def test_all_letters_bonus():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Place a 7-letter word
    move_letters = [(7, 7, "T"), (7, 8, "E"), (7, 9, "S"), (7, 10, "T"), (7, 11, "I"), (7, 12, "N"), (7, 13, "G")]
    dictionary = set(["TESTING"])
    
    result = calculate_full_move_points(board, move_letters, LETTER_POINTS, BOARD_MULTIPLIERS, dictionary)
    assert result["valid"]
    assert result["total"] > 0
    assert "TESTING" in [word for word, _ in result["words"]]

def test_validate_words():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Test with valid word
    move_letters = [(7, 7, "T"), (7, 8, "E"), (7, 9, "S"), (7, 10, "T")]
    player_rack = ["T", "E", "S", "T"]
    dictionary = set(["TEST"])
    
    is_valid, reason = validate_move(board, move_letters, player_rack, dictionary)
    assert is_valid
    
    # Test with invalid word
    move_letters = [(7, 7, "X"), (7, 8, "Y"), (7, 9, "Z")]
    player_rack = ["X", "Y", "Z"]
    dictionary = set(["TEST"])
    
    is_valid, reason = validate_move(board, move_letters, player_rack, dictionary)
    assert not is_valid

def test_validate_words_unauthorized():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Test with valid word but unauthorized player
    move_letters = [(7, 7, "T"), (7, 8, "E"), (7, 9, "S"), (7, 10, "T")]
    player_rack = ["A", "B", "C"]  # Different rack
    dictionary = set(["TEST"])
    
    is_valid, reason = validate_move(board, move_letters, player_rack, dictionary)
    assert not is_valid
    assert "nicht" in reason

def test_validate_words_with_placements():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Test with valid word and valid placement
    move_letters = [(7, 7, "T"), (7, 8, "E"), (7, 9, "S"), (7, 10, "T")]
    player_rack = ["T", "E", "S", "T"]
    dictionary = set(["TEST"])
    
    is_valid, reason = validate_move(board, move_letters, player_rack, dictionary)
    assert is_valid
    
    # Calculate points
    result = calculate_full_move_points(board, move_letters, LETTER_POINTS, BOARD_MULTIPLIERS, dictionary)
    assert result["valid"]
    assert result["total"] > 0
    assert "TEST" in [word for word, _ in result["words"]]

def test_find_word_placements_first_move():
    """Test finding valid placements for the first move."""
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    word = "TEST"
    player_rack = list("TEST")
    dictionary = set(["TEST"])
    
    # Try placing horizontally through center
    move_letters = [(7, 6, "T"), (7, 7, "E"), (7, 8, "S"), (7, 9, "T")]
    result = calculate_full_move_points(board, move_letters, LETTER_POINTS, BOARD_MULTIPLIERS, dictionary)
    assert result["valid"], f"Move should be valid, got error: {result.get('error', '')}"
    
    # Try placing vertically through center
    move_letters = [(5, 7, "T"), (6, 7, "E"), (7, 7, "S"), (8, 7, "T")]
    result = calculate_full_move_points(board, move_letters, LETTER_POINTS, BOARD_MULTIPLIERS, dictionary)
    assert result["valid"], f"Move should be valid, got error: {result.get('error', '')}"

def test_find_word_placements_subsequent_move():
    """Test finding valid placements for subsequent moves."""
    # Create a board with an existing word
    board = [[None for _ in range(15)] for _ in range(15)]
    board[7][7] = "T"
    board[7][8] = "E"
    board[7][9] = "S"
    board[7][10] = "T"
    
    word = "BEST"
    player_rack = list("BEST")
    dictionary = set(["BEST", "TEST"])
    
    # Try placing vertically connecting to the existing word (using the E)
    # Place B-E-S-T vertically where E connects to existing E at (7,8)
    move_letters = [(6, 8, "B"), (8, 8, "S"), (9, 8, "T")]  # Skip (7,8) since E is already there
    result = calculate_full_move_points(board, move_letters, LETTER_POINTS, BOARD_MULTIPLIERS, dictionary)
    assert result["valid"], f"Move should be valid, got error: {result.get('error', '')}"