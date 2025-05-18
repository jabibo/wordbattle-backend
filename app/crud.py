from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Game, Move

async def get_game(db: AsyncSession, game_id: str):
    result = await db.execute(select(Game).where(Game.id == game_id))
    return result.scalars().first()

async def add_move(db: AsyncSession, game_id: str, player_id: int, move_data: str):
    new_move = Move(game_id=game_id, player_id=player_id, move_data=move_data)
    db.add(new_move)
    await db.flush()
    return new_move
