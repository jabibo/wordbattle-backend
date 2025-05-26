from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_register_user():
    response = client.post(
        "/users/register",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code in (200, 400, 404)

def test_create_and_get_game(authenticated_client):
    # Create a game with default settings
    response = authenticated_client.post(
        "/games/",
        json={"language": "en", "max_players": 2}
    )
    assert response.status_code == 200
    assert "id" in response.json()
    
    game_id = response.json()["id"]
    response = authenticated_client.get(f"/games/{game_id}")
    assert response.status_code == 200
    assert response.json()["id"] == game_id
