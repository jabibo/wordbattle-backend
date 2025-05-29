import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token, create_test_user
from app.models.game import GameStatus
from app.game_logic.game_state import GamePhase

client = TestClient(app)

def test_letter_exchange():
    """Test that letter exchange works correctly."""
    # Create a user
    username = f"exchange_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a game and join
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers, json=game_data)
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]

    # Create second player and join
    username2 = f"exchange_test2_{uuid.uuid4().hex[:6]}"
    response = create_test_user(client, username2, password)
    assert response.status_code == 200
    token2 = get_test_token(username2)
    headers2 = {"Authorization": f"Bearer {token2}"}
    join_response = client.post(f"/games/{game_id}/join", headers=headers2)
    assert join_response.status_code == 200

    # Verify game state before starting
    game_state = client.get(f"/games/{game_id}", headers=headers).json()
    assert game_state["phase"] == GamePhase.NOT_STARTED.value
    assert game_state["status"] == GameStatus.READY.value
    assert len(game_state["players"]) == 2

    # Start game
    start_response = client.post(f"/games/{game_id}/start", headers=headers)
    assert start_response.status_code == 200

    # Verify game state after starting
    game_state = client.get(f"/games/{game_id}", headers=headers).json()
    assert game_state["phase"] == GamePhase.IN_PROGRESS.value
    assert game_state["status"] == GameStatus.IN_PROGRESS.value
    
    # Get the requesting user's rack (only visible to the user themselves)
    creator_id = str(game_state["creator_id"])
    initial_rack = game_state["players"][creator_id]["rack"]
    assert initial_rack is not None, "Creator's rack should not be None"
    assert len(initial_rack) == 7, "Initial rack should have 7 letters"

    # Exchange letters
    letters_to_exchange = list(initial_rack[:3])  # Exchange first 3 letters
    
    # Check if it's the creator's turn, if not, use the current player's headers
    current_player_id = game_state["current_player_id"]
    if current_player_id == game_state["creator_id"]:
        # Creator's turn, use original headers
        exchange_headers = headers
    else:
        # It's the second player's turn, use their headers
        exchange_headers = headers2
        # Get the current player's rack
        game_state_for_current = client.get(f"/games/{game_id}", headers=headers2).json()
        current_player_rack = game_state_for_current["players"][str(current_player_id)]["rack"]
        letters_to_exchange = list(current_player_rack[:3])
    
    exchange_response = client.post(
        f"/games/{game_id}/exchange",
        json={"letters_to_exchange": letters_to_exchange},  # API expects embedded format
        headers=exchange_headers
    )
    assert exchange_response.status_code == 200

    # Verify rack changed
    game_state_after = client.get(f"/games/{game_id}", headers=exchange_headers).json()
    current_player_id_after = str(game_state_after["current_player_id"])
    
    # The current player should have changed after the exchange (turn advanced)
    # So we need to check the previous player's rack
    if current_player_id == game_state["creator_id"]:
        # Creator made the exchange, check creator's rack
        new_rack = game_state_after["players"][str(game_state["creator_id"])]["rack"]
        original_rack = initial_rack
    else:
        # Second player made the exchange, check their rack
        new_rack = game_state_after["players"][str(current_player_id)]["rack"]
        original_rack = current_player_rack
    
    assert new_rack != original_rack, "Rack should be different after exchange"
    assert len(new_rack) == len(original_rack), "Rack size should remain the same"

def test_deal_letters():
    """Test dealing initial letters to players."""
    # Create two users
    username1 = f"user1_{uuid.uuid4().hex[:6]}"
    username2 = f"user2_{uuid.uuid4().hex[:6]}"
    password = "secret"
    
    # Register users
    response = create_test_user(client, username1, password)
    assert response.status_code == 200
    response = create_test_user(client, username2, password)
    assert response.status_code == 200
    
    token1 = get_test_token(username1)
    token2 = get_test_token(username2)
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Create game with first user's auth
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers1, json=game_data)
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]
    
    # Second player joins
    join_response = client.post(f"/games/{game_id}/join", headers=headers2)
    assert join_response.status_code == 200
    
    # Start game
    start_response = client.post(f"/games/{game_id}/start", headers=headers1)
    assert start_response.status_code == 200
    
    # Get game state
    game_state = client.get(f"/games/{game_id}", headers=headers1).json()
    
    # Find the authenticated user's rack
    initial_rack = None
    for player_id, player_data in game_state["players"].items():
        if len(player_data["rack"]) > 0:  # Only the authenticated user's rack is visible
            initial_rack = player_data["rack"]
            break
    
    assert initial_rack is not None, "Authenticated user should have a visible rack"
    assert len(initial_rack) == 7, "Initial rack should have 7 letters"
    
    # Get rack through rack endpoint
    rack_response = client.get(f"/rack/{game_id}", headers=headers1)
    assert rack_response.status_code == 200
    rack_data = rack_response.json()
    assert rack_data["rack"] == initial_rack, "Rack endpoint should match game state"

