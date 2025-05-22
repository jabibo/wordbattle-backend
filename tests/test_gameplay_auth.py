from fastapi.testclient import TestClient
from app.main import app
import uuid
import json

client = TestClient(app)

def test_join_deal_exchange_authenticated():
    username = f"authuser_{uuid.uuid4().hex[:6]}"
    password = "secret"

    # Registrierung via API
    register = client.post("/users/register", json={"username": username, "password": password})
    assert register.status_code in (200, 400)

    # Token holen
    token_res = client.post("/auth/token", data={"username": username, "password": password})
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

        # Spiel erstellen
    res = client.post("/games/")
    assert res.status_code == 200
    game_id = res.json()["id"]

    # Join
    join = client.post(f"/games/{game_id}/join", headers=headers)
    assert join.status_code == 200
    assert "rack" in join.json()

    # Deal
    deal = client.post(f"/games/{game_id}/deal", headers=headers)
    assert deal.status_code == 200
    assert "new_rack" in deal.json()

    # Exchange
    letters = deal.json()["new_rack"][:2]
    exchange = client.post(f"/games/{game_id}/exchange", params={"letters": letters}, headers=headers)
    assert exchange.status_code == 200
    assert "new_rack" in exchange.json()
