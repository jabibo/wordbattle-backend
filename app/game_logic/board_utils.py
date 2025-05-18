from typing import List, Tuple, Optional

def apply_move_to_board(
    board: List[List[Optional[str]]],
    move_letters: List[Tuple[int, int, str]]
) -> List[List[Optional[str]]]:
    board_copy = [row[:] for row in board]
    for r, c, letter in move_letters:
        board_copy[r][c] = letter.upper()
    return board_copy
