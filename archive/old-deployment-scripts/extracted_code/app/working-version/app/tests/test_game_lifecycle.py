import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token, create_test_user
from app.models.game import GameStatus

client = TestClient(app)

def test_complete_game_lifecycle(authenticated_client, authenticated_client2):
    """Test a complete game lifecycle from creation to completion."""
    # Create a game with the first user
    game_data = {"language": "en", "max_players": 2}
    game_response = authenticated_client.post("/games/", json=game_data)
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]
    
    # Get game state
    game_state = authenticated_client.get(f"/games/{game_id}")
    assert game_state.status_code == 200
    assert game_state.json()["phase"] == "not_started"
    
    # Creator is already a player, so second player joins
    join_response = authenticated_client2.post(f"/games/{game_id}/join")
    assert join_response.status_code == 200
    
    # Start game (only creator can start)
    start_response = authenticated_client.post(f"/games/{game_id}/start")
    assert start_response.status_code == 200
    
    # Check game state after start
    game_state = authenticated_client.get(f"/games/{game_id}")
    assert game_state.status_code == 200
    assert game_state.json()["phase"] == "in_progress"

def test_game_state_transitions(authenticated_client, authenticated_client2):
    """Test that game state transitions correctly."""
    # Create a game with the first user
    game_data = {"language": "en", "max_players": 2}
    game_response = authenticated_client.post("/games/", json=game_data)
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]

    # Check initial state
    game_state = authenticated_client.get(f"/games/{game_id}")
    assert game_state.status_code == 200
    assert game_state.json()["phase"] == "not_started"

    # Second player joins (creator is already a player)
    join_response = authenticated_client2.post(f"/games/{game_id}/join")
    assert join_response.status_code == 200

    # Check state after join
    game_state = authenticated_client.get(f"/games/{game_id}")
    assert game_state.status_code == 200
    assert game_state.json()["phase"] == "not_started"
    assert len(game_state.json()["players"]) == 2, "Should have two players after join"

    # Start game
    start_response = authenticated_client.post(f"/games/{game_id}/start")
    assert start_response.status_code == 200

    # Check state after start
    game_state = authenticated_client.get(f"/games/{game_id}")
    assert game_state.status_code == 200
    assert game_state.json()["phase"] == "in_progress"
    
    # Verify both players have racks (but only current user's rack is visible)
    game_data = game_state.json()
    current_user_id = None
    for player_id, player_data in game_data["players"].items():
        assert "rack" in player_data, f"Player {player_id} should have a rack field"
        # Only the current user's rack should be visible as a list of letters
        if isinstance(player_data["rack"], list) and len(player_data["rack"]) > 0:
            current_user_id = player_id
            assert len(player_data["rack"]) == 7, f"Current player {player_id} should have 7 letters"
    
    assert current_user_id is not None, "At least one player should have a visible rack"

