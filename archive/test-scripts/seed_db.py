
from app.database import SessionLocal
from app.models import User, Game, Player
import json
import uuid

db = SessionLocal()

user = User(username="demo", hashed_password="demo")
db.add(user)
db.commit()
db.refresh(user)

game = Game(id=str(uuid.uuid4()), state=json.dumps([[None]*15 for _ in range(15)]), current_player_id=user.id)
db.add(game)
db.commit()
db.refresh(game)

rack = "HALLOTE"
player = Player(user_id=user.id, game_id=game.id, rack=rack, score=0)
db.add(player)
db.commit()

print("Demo-Spiel erstellt:")
print(f"User ID: {user.id}")
print(f"Game ID: {game.id}")
print(f"Rack: {rack}")

db.close()
