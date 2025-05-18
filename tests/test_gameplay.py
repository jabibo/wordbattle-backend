from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Game, User

client = TestClient(app)

def test_join_deal_exchange():
    db = SessionLocal()

    # Setup: User + Game
    user = User(username="testspieler", hashed_password="test")
    db.add(user)
    db.commit()
    db.refresh(user)

    game = Game(id="game123", state="[]", current_player_id=user.id)
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
