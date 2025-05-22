from typing import List, Tuple, Optional, Set

def validate_move(
    board: List[List[Optional[str]]],
    move_letters: List[Tuple[int, int, str]],
    player_rack: List[str],
    dictionary: Set[str]
) -> Tuple[bool, str]:
    if not move_letters:
        return False, "Kein Buchstabe gelegt."

    # Prüfe: Koordinaten sind innerhalb des Spielfelds
    board_size = len(board)
    for r, c, _ in move_letters:
        if r < 0 or r >= board_size or c < 0 or c >= board_size:
            return False, f"Koordinaten ({r},{c}) außerhalb des Spielfelds."

    # Prüfe: Nur eine Zeile oder Spalte
    rows = {r for r, c, l in move_letters}
    cols = {c for r, c, l in move_letters}
    if len(rows) != 1 and len(cols) != 1:
        return False, "Buchstaben müssen in einer Zeile oder Spalte liegen."

    # Prüfe: Felder sind leer
    for r, c, _ in move_letters:
        if board[r][c] not in (None, "", " "):
            return False, f"Feld ({r},{c}) ist bereits belegt."

    # Prüfe: Spieler hat die Buchstaben
    rack_copy = player_rack[:]
    for _, _, l in move_letters:
        if l in rack_copy:
            rack_copy.remove(l)
        elif '?' in rack_copy:  # Joker ersetzen
            rack_copy.remove('?')
        else:
            return False, f"Spieler hat Buchstabe {l} nicht."

    # Prüfe: Anbindung an bestehendes Wort (außer bei Spielstart)
    board_has_letters = any(any(cell for cell in row) for row in board)
    if board_has_letters:
        adjacent = False
        for r, c, _ in move_letters:
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                rr, cc = r + dr, c + dc
                if 0 <= rr < board_size and 0 <= cc < board_size and board[rr][cc]:
                    adjacent = True
        if not adjacent:
            return False, "Zug muss an bestehendem Wort angrenzen."

    return True, "Zug ist gültig."