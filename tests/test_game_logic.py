from app.game_logic.validate_move import validate_move
from app.game_logic.full_points import calculate_full_move_points
from app.game_logic.board_utils import apply_move_to_board

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
    
    # Define a move on a word multiplier
    move_letters = [(0, 0, "H"), (0, 1, "A"), (0, 2, "T")]
    
    # Define letter points and multipliers
    letter_points = {'A': 1, 'H': 2, 'T': 1}
    multipliers = {(0, 0): "WW"}  # Triple word score at (0,0)
    dictionary = set(["HAT"])
    
    result = calculate_full_move_points(board, move_letters, letter_points, multipliers, dictionary)
    
    assert result["valid"]
    assert result["total"] > 4  # Should be more than sum of letter points due to multiplier

def test_all_letters_bonus():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Define a move using all 7 letters
    move_letters = [
        (7, 7, "S"), (7, 8, "C"), (7, 9, "R"), (7, 10, "A"), 
        (7, 11, "B"), (7, 12, "B"), (7, 13, "L")
    ]
    
    # Define letter points and multipliers
    letter_points = {
        'S': 1, 'C': 4, 'R': 1, 'A': 1, 'B': 3, 'L': 2
    }
    multipliers = {}
    dictionary = set(["SCRABBL"])
    
    result = calculate_full_move_points(board, move_letters, letter_points, multipliers, dictionary)
    
    assert result["valid"]
    base_points = sum(letter_points[letter] for _, _, letter in move_letters)
    assert result["total"] >= base_points + 50  # Should include 50-point bonus