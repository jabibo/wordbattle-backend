from pydantic import BaseModel
from typing import Optional

class MoveCreate(BaseModel):
    move_data: str

class MoveOut(MoveCreate):
    id: int
    game_id: str
    player_id: int
    timestamp: str
