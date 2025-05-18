from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_valid_move_flow():
    # Spiel erstellen
    response = client.post("/games/")
    assert response.status_code == 200
    game_id = response.json()["id"]

    # Beispielhafter Zug (HALLO von 7,7 horizontal)
    move = [
        {"row": 7, "col": 7, "letter": "H"},
        {"row": 7, "col": 8, "letter": "A"},
        {"row": 7, "col": 9, "letter": "L"},
        {"row": 7, "col": 10, "letter": "L"},
        {"row": 7, "col": 11, "letter": "O"}
    ]

    move_response = client.post(f"/games/{game_id}/move", json={"move_data": move})
    assert move_response.status_code == 200
    data = move_response.json()
    assert data["points"] > 0
    assert "HALLO" in [w[0] for w in data["words"]]
