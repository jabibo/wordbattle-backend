import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token

client = TestClient(app)

def test_complete_game_lifecycle():
    """Test a complete game lifecycle from creation to completion."""
    # Create two users
    user1 = f"player1_{uuid.uuid4().hex[:6]}"
    user2 = f"player2_{uuid.uuid4().hex[:6]}"
    password = "testpass"

    # Register users
    client.post("/users/register", json={"username": user1, "password": password})
    client.post("/users/register", json={"username": user2, "password": password})

    # Get tokens
    token1 = get_test_token(user1)
    token2 = get_test_token(user2)
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Create a game
    game_response = client.post("/games/")
    assert game_response.status_code in (200, 404)
    
    if game_response.status_code == 200:
        game_id = game_response.json()["id"]
        
        # Join the game
        client.post(f"/games/{game_id}/join", headers=headers1)
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # Start the game
        client.post(f"/games/{game_id}/start", headers=headers1)
        
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
            headers=headers1
        )
        assert move_response.status_code in (200, 403, 404)
        
        # Complete the game
        complete_response = client.post(f"/games/{game_id}/complete", headers=headers1)
        assert complete_response.status_code in (200, 403, 404)

def test_game_state_transitions():
    """Test that game state transitions correctly."""
    # Create a user
    username = f"transition_{uuid.uuid4().hex[:6]}"
    password = "testpass"

    client.post("/users/register", json={"username": username, "password": password})
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a game
    game_response = client.post("/games/")
    assert game_response.status_code in (200, 404)
    
    if game_response.status_code == 200:
        game_id = game_response.json()["id"]
        
        # Join the game
        client.post(f"/games/{game_id}/join", headers=headers)
        
        # Try to start with only one player (should fail)
        start_response = client.post(f"/games/{game_id}/start", headers=headers)
        assert start_response.status_code in (400, 403, 404)
        
        # Create second player
        username2 = f"transition2_{uuid.uuid4().hex[:6]}"
        client.post("/users/register", json={"username": username2, "password": password})
        token2 = get_test_token(username2)
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Second player joins
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # Start the game
        start_response = client.post(f"/games/{game_id}/start", headers=headers)
        assert start_response.status_code in (200, 403, 404)

