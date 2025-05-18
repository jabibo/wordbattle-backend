from typing import List, Tuple, Dict, Optional, Set

LETTER_POINTS = {
    'A': 1, 'B': 3, 'C': 4, 'D': 1, 'E': 1, 'F': 4, 'G': 2, 'H': 2, 'I': 1, 'J': 6, 'K': 4, 'L': 2,
    'M': 3, 'N': 1, 'O': 2, 'P': 4, 'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 6, 'W': 3, 'X': 8,
    'Y': 10, 'Z': 3, '?': 0, '*': 0
}

def is_blank(letter: str) -> bool:
    return letter in ('?', '*')

def get_word_horizontal(board: List[List[Optional[str]]], row: int, col: int) -> Tuple[str, List[Tuple[int,int]]]:
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
    board_copy = [row[:] for row in board]
    for r, c, l in move_letters:
        board_copy[r][c] = l.upper()
    rows = {r for (r, c, l) in move_letters}
    cols = {c for (r, c, l) in move_letters}
    is_row = len(rows) == 1
    is_col = len(cols) == 1
    words_and_coords = []

    if is_row:
        row = next(iter(rows))
        min_c = min(cols)
        main_word, main_coords = get_word_horizontal(board_copy, row, min_c)
    elif is_col:
        col = next(iter(cols))
        min_r = min(rows)
        main_word, main_coords = get_word_vertical(board_copy, min_r, col)
    else:
        (r, c, l) = move_letters[0]
        main_word, main_coords = get_word_horizontal(board_copy, r, c)
        if len(main_word) == 1:
            main_word, main_coords = get_word_vertical(board_copy, r, c)
    if len(main_word) > 1:
        words_and_coords.append((main_word, main_coords))

    for r, c, l in move_letters:
        if is_row:
            w, coords = get_word_vertical(board_copy, r, c)
        else:
            w, coords = get_word_horizontal(board_copy, r, c)
        if len(w) > 1 and (w, coords) not in words_and_coords:
            words_and_coords.append((w, coords))

    for word, _ in words_and_coords:
        if not (word in dictionary or word.upper() in dictionary or word.lower() in dictionary):
            return {
                "valid": False,
                "error": f"Wort nicht gültig: '{word}'"
            }

    total_points = 0
    word_points_list = []
    details = []
    new_positions = {(r, c) for (r, c, _) in move_letters}

    for word, coords in words_and_coords:
        word_pts = 0
        word_multi = 1
        for (r, c) in coords:
            letter = board_copy[r][c]
            base_points = 0 if is_blank(letter) else letter_points.get(letter.upper(), 0)
            letter_multi = 1
            local_word_multi = 1
            if (r, c) in new_positions:
                multi = multipliers.get((r, c))
                if multi == "BL": letter_multi = 2
                elif multi == "BW": letter_multi = 3
                elif multi == "WL": local_word_multi = 2
                elif multi == "WW": local_word_multi = 3
            word_pts += base_points * letter_multi
            word_multi *= local_word_multi
        word_pts *= word_multi
        word_points_list.append((word, word_pts))
        total_points += word_pts

    if len(move_letters) == 7:
        total_points += 50

    return {
        "valid": True,
        "total": total_points,
        "words": word_points_list,
        "details": details
    }
