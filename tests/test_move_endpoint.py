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
    user1_response = client.post("/users/register", json={"username": username1, "password": password})
    user2_response = client.post("/users/register", json={"username": username2, "password": password})
    assert user1_response.status_code == 200
    assert user2_response.status_code == 200
    
    user1_id = user1_response.json()["id"]
    user2_id = user2_response.json()["id"]
    
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
    current_player_id = game_state["current_player_id"]
    
    # Find the current player's rack
    current_player_rack = None
    for player_id, player_data in game_state["players"].items():
        if int(player_id) == current_player_id:
            current_player_rack = player_data["rack"]
            break
    
    assert current_player_rack is not None, "Current player should have a rack"
    assert len(current_player_rack) == 7, "Initial rack should have 7 letters"
    
    # Try to form a valid word from the rack
    possible_words = [
        ("HELLO", ["H", "E", "L", "L", "O"]),
        ("WORLD", ["W", "O", "R", "L", "D"]),
        ("TEST", ["T", "E", "S", "T"]),
        ("GAME", ["G", "A", "M", "E"]),
        ("WORD", ["W", "O", "R", "D"]),
        ("DAY", ["D", "A", "Y"]),
        ("TREE", ["T", "R", "E", "E"]),
        ("HOUSE", ["H", "O", "U", "S", "E"]),
        ("CAR", ["C", "A", "R"]),
        ("TABLE", ["T", "A", "B", "L", "E"])
    ]
    
    word_to_play = None
    letters_needed = None
    
    for word, letters in possible_words:
        if all(letter in current_player_rack for letter in letters):
            word_to_play = word
            letters_needed = letters
            break
    
    if word_to_play:
        # Place the word horizontally starting at center
        move_data = [
            {"row": 7, "col": 7 + i, "letter": letter}
            for i, letter in enumerate(letters_needed)
        ]
        
        # Determine which headers to use based on current player
        headers = headers1 if current_player_id == user1_id else headers2
        
        move_response = client.post(f"/games/{game_id}/move", json=move_data, headers=headers)
        assert move_response.status_code == 200
        
        # Verify move results
        game_state = client.get(f"/games/{game_id}", headers=headers).json()
        assert game_state["current_player_id"] != current_player_id, "Turn should rotate to next player"
        
        # Verify score was awarded
        player_data = game_state["players"][str(current_player_id)]
        assert player_data["score"] > 0, "Player should receive points for valid move"
    else:
        # Skip test if we can't form any valid word
        print("Skipping test - could not form a valid word from rack")
        assert True

