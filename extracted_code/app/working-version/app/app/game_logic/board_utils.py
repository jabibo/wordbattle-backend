from typing import List, Tuple, Optional, Dict, Set
from app.game_logic.validate_move import validate_move
from app.game_logic.letter_bag import LETTER_DISTRIBUTION
from app.game_logic.full_points import calculate_full_move_points

# Standard Scrabble board multipliers
# WW = Triple Word Score (3x word multiplier)
# WL = Double Word Score (2x word multiplier)
# BW = Triple Letter Score (3x letter multiplier)
# BL = Double Letter Score (2x letter multiplier)

BOARD_MULTIPLIERS = {
    # Triple Word Score
    (0, 0): "WW", (0, 7): "WW", (0, 14): "WW",
    (7, 0): "WW", (7, 14): "WW",
    (14, 0): "WW", (14, 7): "WW", (14, 14): "WW",
    # Double Word Score
    (1, 1): "WL", (1, 13): "WL",
    (2, 2): "WL", (2, 12): "WL",
    (3, 3): "WL", (3, 11): "WL",
    (4, 4): "WL", (4, 10): "WL",
    (7, 7): "WL",  # Center tile
    (10, 4): "WL", (10, 10): "WL",
    (11, 3): "WL", (11, 11): "WL",
    (12, 2): "WL", (12, 12): "WL",
    (13, 1): "WL", (13, 13): "WL",
    # Triple Letter Score
    (1, 5): "BW", (1, 9): "BW",
    (5, 1): "BW", (5, 5): "BW", (5, 9): "BW", (5, 13): "BW",
    (9, 1): "BW", (9, 5): "BW", (9, 9): "BW", (9, 13): "BW",
    (13, 5): "BW", (13, 9): "BW",
    # Double Letter Score
    (0, 3): "BL", (0, 11): "BL",
    (2, 6): "BL", (2, 8): "BL",
    (3, 0): "BL", (3, 7): "BL", (3, 14): "BL",
    (6, 2): "BL", (6, 6): "BL", (6, 8): "BL", (6, 12): "BL",
    (7, 3): "BL", (7, 11): "BL",
    (8, 2): "BL", (8, 6): "BL", (8, 8): "BL", (8, 12): "BL",
    (11, 0): "BL", (11, 7): "BL", (11, 14): "BL",
    (12, 6): "BL", (12, 8): "BL",
    (14, 3): "BL", (14, 11): "BL"
}

def apply_move_to_board(
    board: List[List[Optional[str]]],
    move_letters: List[Tuple[int, int, str]]
) -> List[List[Optional[str]]]:
    board_copy = [row[:] for row in board]
    for r, c, letter in move_letters:
        board_copy[r][c] = letter.upper()
    return board_copy

def find_word_placements(
    board: List[List[Optional[str]]],
    word: str,
    player_rack: List[str],
    dictionary: Set[str],
    is_first_move: bool = False,
    language: str = "en"  # Add language parameter for scoring
) -> List[Dict]:
    """
    Find all valid positions where a word can be placed on the board.
    
    Args:
        board: The current game board
        word: The word to place
        player_rack: The player's current rack of letters
        dictionary: Set of valid words
        is_first_move: Whether this is the first move of the game
        language: Game language for scoring (default: "en")
    
    Returns:
        List of dictionaries containing valid placements with:
        - position: (row, col) of start position
        - direction: "horizontal" or "vertical"
        - uses_board_letters: list of positions of board letters used
        - required_letters: list of letters needed from rack
        - score_preview: dictionary containing score details
    """
    placements = []
    word = word.upper()
    board_size = len(board)
    
    # Get letter points for the game language
    letter_points = LETTER_DISTRIBUTION.get(language, LETTER_DISTRIBUTION["en"])["points"]
    
    # Helper function to check if a position is within board bounds
    def is_within_bounds(row: int, col: int) -> bool:
        return 0 <= row < board_size and 0 <= col < board_size
    
    # Helper function to check if a position is empty or matches the needed letter
    def is_valid_position(row: int, col: int, letter: str) -> bool:
        if not is_within_bounds(row, col):
            return False
        return board[row][col] is None or board[row][col] == letter
    
    # Helper function to check if placement creates only valid words
    def creates_valid_words(row: int, col: int, is_horizontal: bool) -> bool:
        # Create temporary move letters for validation
        move_letters = []
        uses_board_letters = []
        required_letters = []
        
        for i, letter in enumerate(word):
            curr_row = row if not is_horizontal else row + i
            curr_col = col + i if is_horizontal else col
            
            if not is_within_bounds(curr_row, curr_col):
                return False
                
            if board[curr_row][curr_col] is None:
                move_letters.append((curr_row, curr_col, letter))
                required_letters.append(letter)
            elif board[curr_row][curr_col] == letter:
                uses_board_letters.append((curr_row, curr_col))
            else:
                return False
        
        # Check if we have the required letters in rack
        available_letters = player_rack.copy()
        for letter in required_letters:
            if letter not in available_letters:
                return False
            available_letters.remove(letter)
        
        # Validate the move
        is_valid, _ = validate_move(board, move_letters, player_rack, dictionary)
        if is_valid:
            # Calculate score for this placement
            score_result = calculate_full_move_points(board, move_letters, letter_points, BOARD_MULTIPLIERS, dictionary)
            
            # Check if score calculation was successful
            if score_result.get("valid", True):
                total_points = score_result.get("total", 0)
                
                # Add bonus points for using all letters (if applicable)
                uses_all_letters = len(required_letters) == 7
                bonus_points = 50 if uses_all_letters else 0
                if uses_all_letters:
                    total_points += 50
                
                placements.append({
                    "position": (row, col),
                    "direction": "horizontal" if is_horizontal else "vertical",
                    "uses_board_letters": uses_board_letters,
                    "required_letters": required_letters,
                    "score_preview": {
                        "base_points": score_result.get("total", 0),
                        "bonus_points": bonus_points,
                        "total_points": total_points,
                        "words_formed": [word for word, _ in score_result.get("words", [])],
                        "multipliers_used": []  # This info isn't available from the current function
                    }
                })
        return is_valid
    
    # If it's the first move, only check center positions
    if is_first_move:
        center = board_size // 2
        # Try horizontal placement through center
        if len(word) <= board_size:
            start_col = max(0, center - len(word) + 1)
            end_col = min(board_size - len(word) + 1, center + 1)
            for col in range(start_col, end_col):
                creates_valid_words(center, col, True)
        
        # Try vertical placement through center
        if len(word) <= board_size:
            start_row = max(0, center - len(word) + 1)
            end_row = min(board_size - len(word) + 1, center + 1)
            for row in range(start_row, end_row):
                creates_valid_words(row, center, False)
        
        return placements
    
    # For subsequent moves, check all possible positions that connect to existing words
    for row in range(board_size):
        for col in range(board_size):
            if board[row][col] is not None:
                # Check horizontal placements
                for i in range(max(0, col - len(word) + 1), col + 1):
                    if i + len(word) <= board_size:
                        creates_valid_words(row, i, True)
                
                # Check vertical placements
                for i in range(max(0, row - len(word) + 1), row + 1):
                    if i + len(word) <= board_size:
                        creates_valid_words(i, col, False)
    
    # Sort placements by total points in descending order
    placements.sort(key=lambda p: p["score_preview"]["total_points"], reverse=True)
    return placements
