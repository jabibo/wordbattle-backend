from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Scrabble Backend läuft"}

def test_register_user():
    response = client.post("/users/register", json={
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status_code in (200, 400)

def test_create_and_get_game():
    create = client.post("/games/")
    assert create.status_code == 200
    game_id = create.json()["id"]

    get_game = client.get(f"/games/{game_id}")
    assert get_game.status_code == 200
    assert "state" in get_game.json()
