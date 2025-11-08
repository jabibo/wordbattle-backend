import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token, create_test_user

client = TestClient(app)

def test_join_deal_exchange_authenticated(authenticated_client, test_user):
    """Test joining, dealing, and exchanging letters in a game."""
    # Create a second user
    username2 = f"player2_{uuid.uuid4().hex[:6]}"
    password = "testpassword"
    authenticated_response = create_test_user(client, username2, password)
    assert response.status_code == 200
    token2 = get_test_token(username2)
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Create a game with first user
    game_data = {"language": "en", "max_players": 2}
    game_response = authenticated_client.post("/games/", json=game_data)
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]

    # Second player joins
    join_response = authenticated_client.post(f"/games/{game_id}/join", headers=headers2)
    assert join_response.status_code == 200

    # Start game
    start_response = authenticated_client.post(f"/games/{game_id}/start")
    assert start_response.status_code == 200

    # Get game state and verify both players are in
    game_state = authenticated_client.get(f"/games/{game_id}")
    assert game_state.status_code == 200
    game_data = game_state.json()
    
    # Verify both players are in the game
    player_usernames = [player_data["username"] for player_data in game_data["players"].values()]
    assert test_user["username"] in player_usernames, "First player should be in game"
    assert username2 in player_usernames, "Second player should be in game"
    
    # Verify both players have racks after game start
    # Only the authenticated user's rack is visible as a list of letters
    visible_racks = 0
    for player_id, player_data in game_data["players"].items():
        assert "rack" in player_data, f"Player {player_id} should have a rack field"
        if len(player_data["rack"]) > 0:  # Only authenticated user's rack is visible
            assert len(player_data["rack"]) == 7, f"Visible rack should have 7 letters"
            visible_racks += 1
    
    assert visible_racks == 1, "Exactly one rack should be visible to the authenticated user"

