from typing import List

def get_next_player(player_ids: List[int], current_id: int) -> int:
    if current_id not in player_ids:
        return player_ids[0]
    index = player_ids.index(current_id)
    return player_ids[(index + 1) % len(player_ids)]
