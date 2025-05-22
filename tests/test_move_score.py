from fastapi.testclient import TestClient
from app.main import app
import uuid
import json

client = TestClient(app)

def test_move_and_score_rotation():
    # User registration and login
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "secret"
    reg = client.post("/users/register", json={"username": username, "password": password})
    assert reg.status_code in (200, 400)
    token_res = client.post("/auth/token", data={"username": username, "password": password})
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create game
    res = client.post("/games/")
    assert res.status_code == 200
    game_id = res.json()["id"]

    # Join game
    join = client.post(f"/games/{game_id}/join", headers=headers)
    assert join.status_code == 200

    # Example move (HALLO at 7,7 horizontal)
    move = [
        {"row": 7, "col": 7, "letter": "H"},
        {"row": 7, "col": 8, "letter": "A"},
        {"row": 7, "col": 9, "letter": "L"},
        {"row": 7, "col": 10, "letter": "L"},
        {"row": 7, "col": 11, "letter": "O"}
    ]

    response = client.post(
        f"/games/{game_id}/move",
        json={"move_data": move},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["points"] > 0
    assert "HALLO" in [w[0] for w in data["words"]]
