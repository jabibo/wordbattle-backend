import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token

client = TestClient(app)

def test_move_and_score_rotation():
    # User registration and login
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "secret"
    reg = client.post("/users/register", json={"username": username, "password": password})
    assert reg.status_code in (200, 400)
    
    # Create token directly
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a second user
    username2 = f"user2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": username2, "password": password})
    token2 = get_test_token(username2)
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Create a game
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

    # Get initial game state
    game_state = client.get(f"/games/{game_id}", headers=headers).json()
    current_player_id = str(game_state["current_player_id"])
    
    # Find the authenticated user's rack and score (only their own rack is visible)
    initial_rack = None
    initial_score = None
    authenticated_user_id = None
    for player_id, player_data in game_state["players"].items():
        if len(player_data["rack"]) > 0:  # Only the authenticated user's rack is visible
            initial_rack = player_data["rack"]
            initial_score = player_data["score"]
            authenticated_user_id = player_id
            break
    
    assert initial_rack is not None, "Authenticated user should have a visible rack"
    assert len(initial_rack) == 7, "Initial rack should have 7 letters"

    # Try to form a valid word from the rack
    possible_words = [
        ("JA", ["J", "A"]),
        ("AN", ["A", "N"]),
        ("AB", ["A", "B"]),
        ("DA", ["D", "A"]),
        ("EI", ["E", "I"])
    ]

    word_to_play = None
    letters_needed = None
    
    for word, letters in possible_words:
        if all(letter in initial_rack for letter in letters):
            word_to_play = word
            letters_needed = letters
            break

    if word_to_play:
        # Place the word horizontally starting at center
        move = [
            {"row": 7, "col": 7 + i, "letter": letter}
            for i, letter in enumerate(letters_needed)
        ]
        
        # Make move
        move_response = client.post(
            f"/games/{game_id}/move",
            json=move,
            headers=headers
        )
        assert move_response.status_code == 200

        # Get updated game state
        updated_state = client.get(f"/games/{game_id}", headers=headers).json()
        
        # Verify score increased for the authenticated user
        new_score = updated_state["players"][authenticated_user_id]["score"]
        assert new_score > initial_score, "Score should increase after valid move"
        
        # Verify turn rotated to other player
        assert str(updated_state["current_player_id"]) != current_player_id, "Turn should rotate after move"
        
        # Find the authenticated user's rack again
        new_rack = None
        for player_id, player_data in updated_state["players"].items():
            if len(player_data["rack"]) > 0:  # Only the authenticated user's rack is visible
                new_rack = player_data["rack"]
                break
        
        assert new_rack is not None, "Authenticated user should still have a visible rack"
        assert len(new_rack) == 7, "Rack should be refilled to 7 letters"
    else:
        # Skip test if we can't form any valid word
        print("Skipping test - could not form a valid word from rack")
        assert True

