import json
from datetime import datetime
from app.game_logic.game_state import GamePhase, MoveType, Position, PlacedTile

class GameStateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (GamePhase, MoveType)):
            return obj.value
        elif isinstance(obj, Position):
            return {"row": obj.row, "col": obj.col}
        elif isinstance(obj, PlacedTile):
            return {"letter": obj.letter, "is_blank": obj.is_blank, "tile_id": obj.tile_id}
        elif isinstance(obj, set):
            return list(obj)
        return super().default(obj)
