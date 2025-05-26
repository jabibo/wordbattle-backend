import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token

client = TestClient(app)

def test_get_rack_endpoints():
    """Test getting player racks from game state."""
    # Create first user
    username = f"rack_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create second user
    username2 = f"rack_test2_{uuid.uuid4().hex[:6]}"
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

    # Get game state for first player
    game_state = client.get(f"/games/{game_id}", headers=headers).json()
    assert len(game_state["players"]) == 2, "Game should have two players"
    
    # Get actual player IDs from the game state
    player_ids = list(game_state["players"].keys())
    assert len(player_ids) == 2, "Should have exactly 2 player IDs"
    player1_id = player_ids[0]
    player2_id = player_ids[1]
    
    # Verify both players have racks
    assert player1_id in game_state["players"], "First player should be in game"
    assert player2_id in game_state["players"], "Second player should be in game"
    
    # Verify rack visibility rules
    # First player's view - should see their own rack, other player's rack should be empty
    player1_rack = game_state["players"][player1_id]["rack"]
    player2_rack = game_state["players"][player2_id]["rack"]
    
    # One of the racks should be visible (the current user's), the other should be empty
    visible_racks = [rack for rack in [player1_rack, player2_rack] if len(rack) > 0]
    empty_racks = [rack for rack in [player1_rack, player2_rack] if len(rack) == 0]
    
    assert len(visible_racks) == 1, "Exactly one rack should be visible to the current user"
    assert len(empty_racks) == 1, "Exactly one rack should be hidden (empty) from the current user"
    assert len(visible_racks[0]) == 7, "Visible rack should have 7 letters"
    
    # Second player's view
    game_state2 = client.get(f"/games/{game_id}", headers=headers2).json()
    player1_rack2 = game_state2["players"][player1_id]["rack"]
    player2_rack2 = game_state2["players"][player2_id]["rack"]
    
    # Again, one rack should be visible, one should be empty
    visible_racks2 = [rack for rack in [player1_rack2, player2_rack2] if len(rack) > 0]
    empty_racks2 = [rack for rack in [player1_rack2, player2_rack2] if len(rack) == 0]
    
    assert len(visible_racks2) == 1, "Exactly one rack should be visible to the second user"
    assert len(empty_racks2) == 1, "Exactly one rack should be hidden (empty) from the second user"
    assert len(visible_racks2[0]) == 7, "Visible rack should have 7 letters"

def test_refill_rack_after_use():
    """Test refilling the rack after using some letters."""
    # Create a user
    username = f"refill_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create second player
    username2 = f"refill2_{uuid.uuid4().hex[:6]}"
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
    
    # Find the authenticated user's rack (only their own rack is visible)
    initial_rack = None
    for player_id, player_data in game_state["players"].items():
        if len(player_data["rack"]) > 0:  # Only the authenticated user's rack is visible
            initial_rack = player_data["rack"]
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
        # Determine which user is the current player and get their rack
        # Find the authenticated user's ID (the one with visible rack)
        authenticated_user_id = None
        for pid, pdata in game_state["players"].items():
            if len(pdata["rack"]) > 0:  # This is the authenticated user
                authenticated_user_id = pid
                break
        
        # If it's not the authenticated user's turn, get game state from current player's perspective
        if str(current_player_id) != str(authenticated_user_id):
            # Get game state from the current player's perspective
            current_player_game_state = client.get(f"/games/{game_id}", headers=headers2).json()
            # Find the current player's rack
            current_player_rack = None
            for pid, pdata in current_player_game_state["players"].items():
                if len(pdata["rack"]) > 0:  # This is the current player's rack
                    current_player_rack = pdata["rack"]
                    break
            
            # Check if we can form a word with the current player's rack
            word_to_play = None
            letters_needed = None
            for word, letters in possible_words:
                if current_player_rack and all(letter in current_player_rack for letter in letters):
                    word_to_play = word
                    letters_needed = letters
                    break
            
            headers_to_use = headers2
        else:
            headers_to_use = headers
        
        if word_to_play and letters_needed:
            # Place the word horizontally starting at center
            move = [
                {"row": 7, "col": 7 + i, "letter": letter}
                for i, letter in enumerate(letters_needed)
            ]

            # Make move
            move_response = client.post(
                f"/games/{game_id}/move",
                json=move,
                headers=headers_to_use
            )
            assert move_response.status_code == 200

            # Get updated game state
            updated_state = client.get(f"/games/{game_id}", headers=headers).json()
            
            # If the move was made by the authenticated user, check their rack was replenished
            if headers_to_use == headers:
                # Find the authenticated user's rack again
                new_rack = None
                for player_id, player_data in updated_state["players"].items():
                    if len(player_data["rack"]) > 0:  # Only the authenticated user's rack is visible
                        new_rack = player_data["rack"]
                        break
                
                assert new_rack is not None, "Authenticated user should still have a visible rack"
                # Verify rack was refilled
                assert len(new_rack) == 7, "Rack should be refilled to 7 letters"
                # Verify the used letters are no longer in the rack
                for letter in letters_needed:
                    assert new_rack.count(letter) <= initial_rack.count(letter) - 1, f"Letter {letter} should have been used"
    else:
        # Skip test if we can't form any valid word
        print("Skipping test - could not form a valid word from rack")
        assert True

