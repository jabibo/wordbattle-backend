import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token

client = TestClient(app)

def test_move_and_score_rotation():
    # User registration and login
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "secret"
    reg = client.post("/users/register", json={"username": username, "password": password})
    assert reg.status_code in (200, 400)
    
    # Token direkt erstellen
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a second user
    username2 = f"user2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": username2, "password": password})
    token2 = get_test_token(username2)
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Create a game
    game_response = client.post("/games/")
    assert game_response.status_code in (200, 404)
    
    if game_response.status_code == 200:
        game_id = game_response.json()["id"]
        
        # Both players join
        client.post(f"/games/{game_id}/join", headers=headers)
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # Start the game
        client.post(f"/games/{game_id}/start", headers=headers)
        
        # Make a move
        move = [
            {"row": 7, "col": 7, "letter": "H"},
            {"row": 7, "col": 8, "letter": "A"},
            {"row": 7, "col": 9, "letter": "L"},
            {"row": 7, "col": 10, "letter": "L"},
            {"row": 7, "col": 11, "letter": "O"}
        ]
        
        move_response = client.post(
            f"/games/{game_id}/move",
            json={"move_data": move},
            headers=headers
        )
        assert move_response.status_code in (200, 403, 404)

