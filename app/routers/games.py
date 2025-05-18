from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.models import Game
import uuid
import json

router = APIRouter(prefix="/games", tags=["games"])

@router.post("/")
async def create_game(db: AsyncSession = Depends(get_db)):
    new_id = str(uuid.uuid4())
    empty_board = json.dumps([[None for _ in range(15)] for _ in range(15)])
    game = Game(id=new_id, state=empty_board)
    db.add(game)
    await db.commit()
    return {"id": new_id, "state": empty_board}

@router.get("/{game_id}")
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(f"SELECT * FROM games WHERE id = :id", {"id": game_id})
    game = result.first()
    return game or {"error": "not found"}
