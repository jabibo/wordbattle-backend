from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Game, User
import uuid
import json

client = TestClient(app)

def test_join_deal_exchange():
    db = SessionLocal()

    # Setup: User + Game mit eindeutiger ID
    unique_name = f"testspieler_{uuid.uuid4().hex[:6]}"
    user = User(username=unique_name, hashed_password="test")
    db.add(user)
    db.commit()
    db.refresh(user)

    game_id = f"game_{uuid.uuid4().hex[:6]}"
    game = Game(id=game_id, state=json.dumps([[None]*15 for _ in range(15)]), current_player_id=user.id)
    db.add(game)
    db.commit()

    # /join
    join = client.post(f"/games/{game.id}/join/{user.id}")
    assert join.status_code == 200
    assert "rack" in join.json()

    # /deal
    deal = client.post(f"/games/{game.id}/deal/{user.id}")
    assert deal.status_code == 200
    assert "new_rack" in deal.json()

    # /exchange
    rack = deal.json()["new_rack"]
    to_exchange = rack[:2]
    exchange = client.post(f"/games/{game.id}/exchange/{user.id}", params={"letters": to_exchange})
    assert exchange.status_code == 200
    assert "new_rack" in exchange.json()

    db.close()
