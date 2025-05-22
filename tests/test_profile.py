from fastapi.testclient import TestClient
from app.main import app
import uuid
import json

client = TestClient(app)

def test_me_and_my_games():
    username = f"unique_user_{uuid.uuid4().hex[:6]}"
    password = "pw"

    # User registrieren
    res = client.post("/users/register", json={"username": username, "password": password})
    assert res.status_code in (200, 400)

    # Token holen
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # /me
    res = client.get("/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["username"] == username

    # Spiel + Player
    game_id = f"game_{uuid.uuid4().hex[:6]}"
    board = json.dumps([[None]*15 for _ in range(15)])
    res = client.post("/games/")
    assert res.status_code == 200
    game_id = res.json()["id"]
    client.post(f"/games/{game_id}/join", headers=headers)

    # /games/mine
    res = client.get("/games/mine", headers=headers)
    games = res.json()
    if isinstance(games, dict):
        games = [games]
    assert any(g.get("id") == game_id for g in games)
