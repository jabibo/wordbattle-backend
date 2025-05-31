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

    # Prüfe: Wörter sind gültig
    temp_board = [row[:] for row in board]
    for r, c, l in move_letters:
        temp_board[r][c] = l

    # Finde alle Wörter
    words = []
    if len(rows) == 1:  # Horizontal
        row = list(rows)[0]
        start = min(c for _, c, _ in move_letters)
        end = max(c for _, c, _ in move_letters)
        while start > 0 and temp_board[row][start-1] not in (None, "", " "):
            start -= 1
        while end < board_size-1 and temp_board[row][end+1] not in (None, "", " "):
            end += 1
        word = "".join(temp_board[row][c] for c in range(start, end+1) if temp_board[row][c] not in (None, "", " "))
        if len(word) > 1:
            words.append(word)
    else:  # Vertikal
        col = list(cols)[0]
        start = min(r for r, _, _ in move_letters)
        end = max(r for r, _, _ in move_letters)
        while start > 0 and temp_board[start-1][col] not in (None, "", " "):
            start -= 1
        while end < board_size-1 and temp_board[end+1][col] not in (None, "", " "):
            end += 1
        word = "".join(temp_board[r][col] for r in range(start, end+1) if temp_board[r][col] not in (None, "", " "))
        if len(word) > 1:
            words.append(word)

    # Prüfe Kreuzwörter
    for r, c, _ in move_letters:
        # Horizontal
        if len(rows) != 1:  # Nur wenn Hauptwort vertikal
            start = c
            end = c
            while start > 0 and temp_board[r][start-1] not in (None, "", " "):
                start -= 1
            while end < board_size-1 and temp_board[r][end+1] not in (None, "", " "):
                end += 1
            word = "".join(temp_board[r][c] for c in range(start, end+1) if temp_board[r][c] not in (None, "", " "))
            if len(word) > 1:
                words.append(word)
        # Vertikal
        if len(cols) != 1:  # Nur wenn Hauptwort horizontal
            start = r
            end = r
            while start > 0 and temp_board[start-1][c] not in (None, "", " "):
                start -= 1
            while end < board_size-1 and temp_board[end+1][c] not in (None, "", " "):
                end += 1
            word = "".join(temp_board[r][c] for r in range(start, end+1) if temp_board[r][c] not in (None, "", " "))
            if len(word) > 1:
                words.append(word)

    # Prüfe ob alle Wörter im Wörterbuch sind
    for word in words:
        if word not in dictionary:
            return False, f"Wort '{word}' nicht im Wörterbuch."

    return True, "Zug ist gültig."