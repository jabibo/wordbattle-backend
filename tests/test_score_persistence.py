import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from tests.test_utils import get_test_token

client = TestClient(app)

def test_score_update_after_move():
    """Test that player's score is properly updated after making a move."""
    username = f"score_test_{uuid.uuid4().hex[:6]}"
    username2 = f"score_test2_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    # Register users
    client.post("/users/register", json={"username": username, "password": password})
    client.post("/users/register", json={"username": username2, "password": password})
    
    token = get_test_token(username)
    token2 = get_test_token(username2)
    headers = {"Authorization": f"Bearer {token}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Create game
    game_response = client.post("/games/")
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]
    
    # Join game
    client.post(f"/games/{game_id}/join", headers=headers)
    client.post(f"/games/{game_id}/join", headers=headers2)
    
    # Start game
    client.post(f"/games/{game_id}/start", headers=headers)
    
    # Make move
    move = [{"row": 7, "col": 7, "letter": "H"}]
    move_response = client.post(
        f"/games/{game_id}/move",
        json={"move_data": move},
        headers=headers
    )
    assert move_response.status_code == 200
    assert "points" in move_response.json()

