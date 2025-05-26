from typing import List, Tuple, Optional, Dict, Set
from app.game_logic.validate_move import validate_move
from app.game_logic.letter_bag import LETTER_DISTRIBUTION
from app.game_logic.full_points import calculate_full_move_points

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
    
    # Standard Scrabble board multipliers
    multipliers = {
        # Triple Word Score
        (0, 0): "TW", (0, 7): "TW", (0, 14): "TW",
        (7, 0): "TW", (7, 14): "TW",
        (14, 0): "TW", (14, 7): "TW", (14, 14): "TW",
        # Double Word Score
        (1, 1): "DW", (2, 2): "DW", (3, 3): "DW", (4, 4): "DW",
        (1, 13): "DW", (2, 12): "DW", (3, 11): "DW", (4, 10): "DW",
        (13, 1): "DW", (12, 2): "DW", (11, 3): "DW", (10, 4): "DW",
        (13, 13): "DW", (12, 12): "DW", (11, 11): "DW", (10, 10): "DW",
        # Triple Letter Score
        (1, 5): "TL", (1, 9): "TL", (5, 1): "TL", (5, 5): "TL",
        (5, 9): "TL", (5, 13): "TL", (9, 1): "TL", (9, 5): "TL",
        (9, 9): "TL", (9, 13): "TL", (13, 5): "TL", (13, 9): "TL",
        # Double Letter Score
        (0, 3): "DL", (0, 11): "DL", (2, 6): "DL", (2, 8): "DL",
        (3, 0): "DL", (3, 7): "DL", (3, 14): "DL",
        (6, 2): "DL", (6, 6): "DL", (6, 8): "DL", (6, 12): "DL",
        (7, 3): "DL", (7, 11): "DL",
        (8, 2): "DL", (8, 6): "DL", (8, 8): "DL", (8, 12): "DL",
        (11, 0): "DL", (11, 7): "DL", (11, 14): "DL",
        (12, 6): "DL", (12, 8): "DL", (14, 3): "DL", (14, 11): "DL",
    }
    
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
            score_result = calculate_full_move_points(board, move_letters, letter_points, multipliers, dictionary)
            
            # Add bonus points for using all letters (if applicable)
            uses_all_letters = len(required_letters) == 7
            if uses_all_letters:
                score_result["bonus_points"] = 50
                score_result["total"] += 50
            
            placements.append({
                "position": (row, col),
                "direction": "horizontal" if is_horizontal else "vertical",
                "uses_board_letters": uses_board_letters,
                "required_letters": required_letters,
                "score_preview": {
                    "base_points": score_result["total"],
                    "bonus_points": score_result.get("bonus_points", 0),
                    "total_points": score_result["total"],
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
