from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.models import Move
from pydantic import BaseModel
import json
from datetime import datetime

router = APIRouter(prefix="/games", tags=["moves"])

class MoveCreate(BaseModel):
    move_data: str

@router.post("/{game_id}/move")
async def make_move(game_id: str, move: MoveCreate, db: AsyncSession = Depends(get_db)):
    new_move = Move(game_id=game_id, player_id=1, move_data=move.move_data, timestamp=datetime.utcnow())
    db.add(new_move)
    await db.commit()
    return {"message": "Zug gespeichert", "move": move.move_data}
