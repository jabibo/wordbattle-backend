import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from tests.test_utils import get_test_token, create_test_user

client = TestClient(app)

def test_score_update_after_move():
    """Test that player's score is properly updated after making a move."""
    username = f"score_test_{uuid.uuid4().hex[:6]}"
    username2 = f"score_test2_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    # Register users
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    response = create_test_user(client, username2, password)
    assert response.status_code == 200
    
    token = get_test_token(username)
    token2 = get_test_token(username2)
    headers = {"Authorization": f"Bearer {token}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Create game
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers, json=game_data)
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]
    
    # Player 2 joins
    join_response = client.post(f"/games/{game_id}/join", headers=headers2)
    assert join_response.status_code == 200
    
    # Verify game state before starting
    game_state = client.get(f"/games/{game_id}", headers=headers).json()
    assert game_state["status"] == "ready"
    
    # Start game
    start_response = client.post(f"/games/{game_id}/start", headers=headers)
    assert start_response.status_code == 200
    
    # Verify game started
    game_state = client.get(f"/games/{game_id}", headers=headers).json()
    assert game_state["status"] == "in_progress"
    
    # Get current player
    current_player_id = game_state["current_player_id"]
    
    # Set a predetermined rack for the current player to ensure we can make a valid move
    from app.database import SessionLocal
    from app.models import Player
    
    db = SessionLocal()
    try:
        current_player = db.query(Player).filter_by(game_id=game_id, user_id=current_player_id).first()
        if current_player:
            current_player.rack = "SUNXYZW"  # SUN + 4 extra letters to make 7 total
            db.commit()
    finally:
        db.close()
    
    # Get the updated game state to verify our rack change
    if current_player_id == game_state["creator_id"]:
        # Current player is the creator (first user)
        updated_game_state = client.get(f"/games/{game_id}", headers=headers).json()
        current_player_rack = None
        for player_id, player_data in updated_game_state["players"].items():
            if len(player_data["rack"]) > 0:  # Only the authenticated user's rack is visible
                current_player_rack = player_data["rack"]
                break
        headers_to_use = headers
    else:
        # Current player is the second user, get their game state
        updated_game_state = client.get(f"/games/{game_id}", headers=headers2).json()
        current_player_rack = None
        for player_id, player_data in updated_game_state["players"].items():
            if len(player_data["rack"]) > 0:  # Only the authenticated user's rack is visible
                current_player_rack = player_data["rack"]
                break
        headers_to_use = headers2
    
    # Test word validation - try to find a valid word from available letters
    possible_words = [
        ("SUN", ["S", "U", "N"]),
        ("SO", ["S", "O"]),
        ("NO", ["N", "O"]),
        ("ON", ["O", "N"]),
        ("US", ["U", "S"])
    ]
    
    word_to_play = None
    letters_needed = None
    
    for word, letters in possible_words:
        if current_player_rack and all(letter in current_player_rack for letter in letters):
            word_to_play = word
            letters_needed = letters
            print(f"Found valid word '{word}' from rack {current_player_rack}")
            break
    
    # Verify we found a valid word (this tests our word validation logic)
    assert word_to_play is not None, f"Should be able to form a word from rack: {current_player_rack}"
    assert letters_needed is not None, "Should have letters needed for the word"
    
    # Place the word horizontally starting at center
    move_data = [
        {"row": 7, "col": 7 + i, "letter": letter}
        for i, letter in enumerate(letters_needed)
    ]
    
    # Make the move (this tests the move validation and word checking)
    move_response = client.post(f"/games/{game_id}/move", json=move_data, headers=headers_to_use)
    assert move_response.status_code == 200, f"Move should succeed for word '{word_to_play}', got {move_response.status_code}: {move_response.json()}"
    
    # Check score update (this tests score persistence)
    game_state_after = client.get(f"/games/{game_id}", headers=headers_to_use).json()
    player_id_str = str(current_player_id)
    assert game_state_after["players"][player_id_str]["score"] > 0, "Player should have scored points"
    
    # Verify the move response includes score information
    move_response_data = move_response.json()
    assert "points_gained" in move_response_data, "Move response should include points"
    assert move_response_data["points_gained"] > 0, "Should gain points for valid word"
    
    # Verify the score in the game state matches the points gained
    assert game_state_after["players"][player_id_str]["score"] == move_response_data["points_gained"], "Game state score should match points gained"

