from typing import List, Tuple, Dict, Optional, Set

LETTER_POINTS = {
    'A': 1, 'B': 3, 'C': 4, 'D': 1, 'E': 1, 'F': 4, 'G': 2, 'H': 2, 'I': 1, 'J': 6, 'K': 4, 'L': 2,
    'M': 3, 'N': 1, 'O': 2, 'P': 4, 'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 6, 'W': 3, 'X': 8,
    'Y': 10, 'Z': 3, '?': 0, '*': 0
}

def is_blank(letter: str) -> bool:
    return letter in ('?', '*')

def get_word_horizontal(board: List[List[Optional[str]]], row: int, col: int) -> Tuple[str, List[Tuple[int,int]]]:
    """Get a horizontal word at the given position."""
    start = col
    while start > 0 and board[row][start-1] not in (None, "", " "):
        start -= 1
    end = col
    while end < len(board[0])-1 and board[row][end+1] not in (None, "", " "):
        end += 1
    word = ''.join(board[row][c] for c in range(start, end+1) if board[row][c])
    coords = [(row, c) for c in range(start, end+1) if board[row][c]]
    return word, coords

def get_word_vertical(board: List[List[Optional[str]]], row: int, col: int) -> Tuple[str, List[Tuple[int,int]]]:
    """Get a vertical word at the given position."""
    start = row
    while start > 0 and board[start-1][col] not in (None, "", " "):
        start -= 1
    end = row
    while end < len(board)-1 and board[end+1][col] not in (None, "", " "):
        end += 1
    word = ''.join(board[r][col] for r in range(start, end+1) if board[r][col])
    coords = [(r, col) for r in range(start, end+1) if board[r][col]]
    return word, coords

def calculate_full_move_points(
    board: List[List[Optional[str]]],
    move_letters: List[Tuple[int, int, str]],
    letter_points: Dict[str, int],
    multipliers: Dict[Tuple[int,int], str],
    dictionary: Set[str]
) -> Dict:
    """Calculate points for a move including all words formed.
    
    Args:
        board: Current game board
        move_letters: List of (row, col, letter) tuples for the move
        letter_points: Dictionary of letter point values
        multipliers: Dictionary of board multipliers
        dictionary: Set of valid words
    
    Returns:
        Dictionary containing:
        - valid: Whether the move is valid
        - total: Total points scored
        - words: List of (word, points) tuples
        - details: List of scoring details
    """
    print(f"DEBUG: Calculating points for move: {move_letters}")
    print(f"DEBUG: Using letter points: {letter_points}")
    print(f"DEBUG: Using multipliers: {multipliers}")
    
    # Create board copy and apply move
    board_copy = [row[:] for row in board]
    for r, c, l in move_letters:
        if board_copy[r][c] not in (None, "", " "):
            print(f"DEBUG: Error - position ({r}, {c}) already occupied")
            return {"valid": False, "error": "Position already occupied"}
        board_copy[r][c] = l.upper()
        print(f"DEBUG: Placed letter {l.upper()} at ({r}, {c})")
    
    # Find all words formed
    rows = {r for (r, c, l) in move_letters}
    cols = {c for (r, c, l) in move_letters}
    is_row = len(rows) == 1
    is_col = len(cols) == 1
    words_and_coords = []

    # Find main word
    if is_row:
        row = next(iter(rows))
        min_c = min(cols)
        main_word, main_coords = get_word_horizontal(board_copy, row, min_c)
        print(f"DEBUG: Found horizontal word: {main_word} at coords {main_coords}")
    elif is_col:
        col = next(iter(cols))
        min_r = min(rows)
        main_word, main_coords = get_word_vertical(board_copy, min_r, col)
        print(f"DEBUG: Found vertical word: {main_word} at coords {main_coords}")
    else:
        return {"valid": False, "error": "Letters must be placed in a line"}

    if len(main_word) > 1:
        words_and_coords.append((main_word, main_coords))

    # Find crossing words
    for r, c, l in move_letters:
        if is_row:
            w, coords = get_word_vertical(board_copy, r, c)
        else:
            w, coords = get_word_horizontal(board_copy, r, c)
        if len(w) > 1 and (w, coords) not in words_and_coords:
            print(f"DEBUG: Found additional word: {w} at coords {coords}")
            words_and_coords.append((w, coords))

    # Validate all words
    for word, _ in words_and_coords:
        if not (word in dictionary or word.upper() in dictionary or word.lower() in dictionary):
            print(f"DEBUG: Word {word} not found in dictionary")
            return {
                "valid": False,
                "error": f"Word not valid: '{word}'"
            }

    # Calculate points
    total_points = 0
    word_points_list = []
    details = []
    new_positions = {(r, c) for (r, c, _) in move_letters}

    for word, coords in words_and_coords:
        word_pts = 0
        word_multi = 1
        print(f"\nDEBUG: Calculating points for word: {word}")
        
        # Calculate base points with letter multipliers
        for (r, c) in coords:
            letter = board_copy[r][c]
            base_points = 0 if is_blank(letter) else letter_points.get(letter.upper(), 0)
            letter_multi = 1
            local_word_multi = 1
            
            if (r, c) in new_positions:
                multi = multipliers.get((r, c))
                print(f"DEBUG: Position ({r}, {c}) has multiplier {multi}")
                if multi == "BL":  # Double letter score
                    letter_multi = 2
                elif multi == "BW":  # Triple letter score
                    letter_multi = 3
                elif multi == "WL":  # Double word score
                    local_word_multi = 2
                elif multi == "WW":  # Triple word score
                    local_word_multi = 3
            
            points_for_letter = base_points * letter_multi
            print(f"DEBUG: Letter {letter} base points: {base_points}, multiplier: {letter_multi}, total: {points_for_letter}")
            word_pts += points_for_letter
            word_multi *= local_word_multi
        
        # Apply word multiplier
        word_pts *= word_multi
        print(f"DEBUG: Word {word} points: {word_pts} (after word multiplier {word_multi})")
        word_points_list.append((word, word_pts))
        total_points += word_pts

    # Add bonus for using all letters
    if len(move_letters) == 7:
        print("DEBUG: Adding 50 point bonus for using all letters")
        total_points += 50

    print(f"DEBUG: Final total points: {total_points}")
    return {
        "valid": True,
        "total": total_points,
        "words": word_points_list,
        "details": details
    }
