import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from tests.test_utils import get_test_token

client = TestClient(app)

def test_valid_move_flow():
    """Test the complete flow of making a valid move."""
    # Create two users
    username1 = f"user1_{uuid.uuid4().hex[:6]}"
    username2 = f"user2_{uuid.uuid4().hex[:6]}"
    password = "secret"
    
    # Register users
    client.post("/users/register", json={"username": username1, "password": password})
    client.post("/users/register", json={"username": username2, "password": password})
    
    token1 = get_test_token(username1)
    token2 = get_test_token(username2)
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Create game
    game_response = client.post("/games/")
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]
    
    # Join game
    client.post(f"/games/{game_id}/join", headers=headers1)
    client.post(f"/games/{game_id}/join", headers=headers2)
    
    # Try move before starting - should fail
    move = [{"row": 7, "col": 7, "letter": "H"}]
    early_response = client.post(
        f"/games/{game_id}/move",
        json={"move_data": move},
        headers=headers1
    )
    assert early_response.status_code == 400
    
    # Start game
    client.post(f"/games/{game_id}/start", headers=headers1)
    
    # Make valid move
    move_response = client.post(
        f"/games/{game_id}/move",
        json={"move_data": move},
        headers=headers1
    )
    assert move_response.status_code == 200
    assert "points" in move_response.json()
    
    # Try move as wrong player - should fail
    wrong_player_response = client.post(
        f"/games/{game_id}/move",
        json={"move_data": move},
        headers=headers1
    )
    assert wrong_player_response.status_code == 403

