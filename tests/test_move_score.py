from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_move_and_score_rotation():
    res = client.post("/games/")
    assert res.status_code == 200
    game_id = res.json()["id"]

    move = [
        {"row": 7, "col": 7, "letter": "H"},
        {"row": 7, "col": 8, "letter": "A"},
        {"row": 7, "col": 9, "letter": "L"},
        {"row": 7, "col": 10, "letter": "L"},
        {"row": 7, "col": 11, "letter": "O"}
    ]

    response = client.post(f"/games/{game_id}/move", json={"move_data": move})
    assert response.status_code == 200
    data = response.json()
    assert "points" in data
    assert data["points"] > 0
    assert "HALLO" in [w[0] for w in data["words"]]
