from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Player
import uuid
from tests.test_utils import get_test_token

client = TestClient(app)

def test_create_player_and_assign_rack():
    """Test creating a player and assigning an initial rack."""
    # Create a user
    username = f"player_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create second player
    username2 = f"player_test2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": username2, "password": password})
    token2 = get_test_token(username2)
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Create game
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers, json=game_data)
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]

    # Second player joins
    join_response = client.post(f"/games/{game_id}/join", headers=headers2)
    assert join_response.status_code == 200

    # Start game
    start_response = client.post(f"/games/{game_id}/start", headers=headers)
    assert start_response.status_code == 200

    # Get game state and verify racks
    game_state = client.get(f"/games/{game_id}", headers=headers).json()
    
    # Check that the current user (creator) has a rack with 7 letters
    current_player_id = str(game_state["current_player_id"])
    creator_player_data = game_state["players"][str(game_state["creator_id"])]
    assert "rack" in creator_player_data, "Creator should have a rack"
    assert creator_player_data["rack"] is not None, "Creator's rack should not be None"
    assert len(creator_player_data["rack"]) == 7, "Creator's rack should have 7 letters"
    
    # Verify that both players exist in the game
    assert len(game_state["players"]) == 2, "Game should have 2 players"
