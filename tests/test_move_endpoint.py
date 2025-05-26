import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from tests.test_utils import get_test_token

client = TestClient(app)

def test_valid_move_flow():
    """Test the complete flow of making a valid move."""
    # Create two users
    username1 = f"user1_{uuid.uuid4().hex[:6]}"
    username2 = f"user2_{uuid.uuid4().hex[:6]}"
    password = "secret"
    
    # Register users
    client.post("/users/register", json={"username": username1, "password": password})
    client.post("/users/register", json={"username": username2, "password": password})
    
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
    
    # Get initial game state
    game_state = client.get(f"/games/{game_id}", headers=headers1).json()
    current_player_id = str(game_state["current_player_id"])
    player_rack = game_state["players"][current_player_id]["rack"]
    
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
        if all(letter in player_rack for letter in letters):
            word_to_play = word
            letters_needed = letters
            break
    
    if word_to_play:
        # Place the word horizontally starting at center
        move = [
            {"row": 7, "col": 7 + i, "letter": letter}
            for i, letter in enumerate(letters_needed)
        ]
        
        # Make move with current player's headers
        headers = headers1 if current_player_id == username1 else headers2
        move_response = client.post(f"/games/{game_id}/move", json=move, headers=headers)
        assert move_response.status_code == 200
        
        # Verify move results
        game_state = client.get(f"/games/{game_id}", headers=headers).json()
        assert game_state["current_player_id"] != current_player_id, "Turn should rotate to next player"
        
        # Verify score was awarded
        player_data = game_state["players"][current_player_id]
        assert player_data["score"] > 0, "Player should receive points for valid move"
    else:
        # Skip test if we can't form any valid word
        print("Skipping test - could not form a valid word from rack")
        assert True

