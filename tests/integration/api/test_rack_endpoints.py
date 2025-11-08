import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token, create_test_user

client = TestClient(app)

def test_get_rack_endpoints():
    """Test getting player racks from game state."""
    # Create first user
    username = f"rack_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create second user
    username2 = f"rack_test2_{uuid.uuid4().hex[:6]}"
    response = create_test_user(client, username2, password)
    assert response.status_code == 200
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
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create second player
    username2 = f"refill2_{uuid.uuid4().hex[:6]}"
    response = create_test_user(client, username2, password)
    assert response.status_code == 200
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
    
    # Find the authenticated user's ID (only their own rack is visible)
    authenticated_user_id = None
    for player_id, player_data in game_state["players"].items():
        if len(player_data["rack"]) > 0:  # Only the authenticated user's rack is visible
            authenticated_user_id = player_id
            break
    
    assert authenticated_user_id is not None, "Authenticated user should be found"
    
    # Set a predetermined rack that can form the word "ICE" (I, C, E + extra letters)
    # Update the player's rack directly in the database to ensure we can make a valid move
    from app.database import SessionLocal
    from app.models import Player
    
    db = SessionLocal()
    try:
        player = db.query(Player).filter_by(game_id=game_id, user_id=int(authenticated_user_id)).first()
        if player:
            player.rack = "ICEXYZW"  # ICE + 4 extra letters to make 7 total
            db.commit()
    finally:
        db.close()
    
    # Define the word we'll play and the letters needed
    word_to_play = "ICE"
    letters_needed = ["I", "C", "E"]

    # Determine which headers to use based on current player
    if str(current_player_id) != str(authenticated_user_id):
        # Current player is the other user, need to set their rack too
        db = SessionLocal()
        try:
            other_player = db.query(Player).filter_by(game_id=game_id, user_id=int(current_player_id)).first()
            if other_player:
                other_player.rack = "FIREXYZ"  # FIRE + 3 extra letters
                db.commit()
        finally:
            db.close()
        headers_to_use = headers2
        word_to_play = "FIRE"
        letters_needed = ["F", "I", "R", "E"]
    else:
        headers_to_use = headers
    
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
    
    assert move_response.status_code == 200, f"Move should succeed for word '{word_to_play}', got {move_response.status_code}: {move_response.json()}"

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
        # Verify rack was refilled to 7 letters
        assert len(new_rack) == 7, "Rack should be refilled to 7 letters"
        
        # Verify the used letters are no longer in the rack (at least some were used)
        remaining_ice_letters = sum(1 for letter in new_rack if letter in ["I", "C", "E"])
        assert remaining_ice_letters < 3, "Some ICE letters should have been used"

