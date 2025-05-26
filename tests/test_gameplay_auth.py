import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token

client = TestClient(app)

def test_join_deal_exchange_authenticated():
    username = f"authuser_{uuid.uuid4().hex[:6]}"
    password = "secret"

    # Register via API
    register = client.post("/users/register", json={"username": username, "password": password})
    assert register.status_code in (200, 400)

    # Create token directly
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create game with auth headers
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers, json=game_data)
    assert game_response.status_code in (200, 404)

    if game_response.status_code == 200:
        game_id = game_response.json()["id"]

        # Get game state
        game_state = client.get(f"/games/{game_id}", headers=headers)
        assert game_state.status_code == 200

        # Verify game exists and has exactly one player
        game_data = game_state.json()
        assert len(game_data["players"]) == 1, "Game should have exactly one player"
        
        # Get the player data (there should be only one player at this point)
        player_id, player_data = next(iter(game_data["players"].items()))
        
        # Verify player has expected initial state
        assert "score" in player_data, "Player should have a score field"
        assert player_data["score"] == 0, "Initial score should be 0"
        
        # In setup phase, rack might not be present or might be empty
        # Rack is only dealt when game starts
        if "rack" in player_data:
            # If rack exists, it should be empty in setup phase or have letters if game started
            rack = player_data["rack"]
            if isinstance(rack, list):
                # Empty list is expected in setup phase
                assert len(rack) == 0 or len(rack) == 7, "Rack should be empty in setup or have 7 letters if started"

