from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app.models import Game, Move, User

def get_game(db: Session, game_id: str):
    result = db.execute(select(Game).where(Game.id == game_id))
    return result.scalars().first()

def add_move(db: Session, game_id: str, player_id: int, move_data: str):
    move = Move(game_id=game_id, player_id=player_id, move_data=move_data)
    db.add(move)
    db.commit()
    db.refresh(move)
    return move

def get_user_by_username(db: Session, username: str):
    result = db.execute(select(User).where(User.username == username))
    return result.scalars().first()

def create_user(db: Session, username: str, hashed_password: str):
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_game_state(db: Session, game_id: str, new_state: str):
    game = get_game(db, game_id)
    if game:
        game.state = new_state
        db.add(game)
        db.commit()
    return game

def get_moves_for_game(db: Session, game_id: str):
    result = db.execute(select(Move).where(Move.game_id == game_id))
    return result.scalars().all()
