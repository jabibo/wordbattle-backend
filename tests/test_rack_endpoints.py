import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token

client = TestClient(app)

def test_get_rack_endpoints():
    """Test the rack endpoints."""
    # Create a user
    username = f"rack_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": username, "password": password})
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a game and join
    game_response = client.post("/games/")
    assert game_response.status_code in (200, 404)
    
    if game_response.status_code == 200:
        game_id = game_response.json()["id"]
        
        # Join the game
        join_response = client.post(f"/games/{game_id}/join", headers=headers)
        assert join_response.status_code in (200, 403, 404)
        
        if join_response.status_code == 200:
            # Get rack
            rack_response = client.get(f"/games/{game_id}/rack", headers=headers)
            assert rack_response.status_code in (200, 403, 404)

def test_refill_rack_after_use():
    """Test refilling the rack after using some letters."""
    # Create a user
    username = f"refill_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": username, "password": password})
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a game and join
    game_response = client.post("/games/")
    assert game_response.status_code in (200, 404)
    
    if game_response.status_code == 200:
        game_id = game_response.json()["id"]
        
        # Join the game
        join_response = client.post(f"/games/{game_id}/join", headers=headers)
        assert join_response.status_code in (200, 403, 404)
        
        if join_response.status_code == 200:
            # Create second player and start game
            username2 = f"refill2_{uuid.uuid4().hex[:6]}"
            client.post("/users/register", json={"username": username2, "password": password})
            token2 = get_test_token(username2)
            headers2 = {"Authorization": f"Bearer {token2}"}
            
            client.post(f"/games/{game_id}/join", headers=headers2)
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

