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
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers, json=game_data)
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]
    
    # Player 2 joins
    join_response = client.post(f"/games/{game_id}/join", headers=headers2)
    assert join_response.status_code == 200
    
    # Verify game state before starting
    game_state = client.get(f"/games/{game_id}", headers=headers).json()
    assert game_state["status"] == "ready"
    
    # Start game
    start_response = client.post(f"/games/{game_id}/start", headers=headers)
    assert start_response.status_code == 200
    
    # Verify game started
    game_state = client.get(f"/games/{game_id}", headers=headers).json()
    assert game_state["status"] == "in_progress"
    
    # Make a move
    move_data = [
        {"row": 7, "col": 7, "letter": "T"},
        {"row": 7, "col": 8, "letter": "E"},
        {"row": 7, "col": 9, "letter": "S"},
        {"row": 7, "col": 10, "letter": "T"}
    ]
    move_response = client.post(f"/games/{game_id}/move", json=move_data, headers=headers)
    assert move_response.status_code == 200
    
    # Check score update
    game_state = client.get(f"/games/{game_id}", headers=headers).json()
    player_id = str(game_state["current_player_id"])  # Convert to string since JSON keys are strings
    assert game_state["players"][player_id]["score"] > 0

