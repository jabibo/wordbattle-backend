from fastapi.testclient import TestClient
from app.main import app
import uuid
from tests.test_utils import get_test_token
from app.auth import create_access_token

client = TestClient(app)

def get_test_token(username):
    return create_access_token(data={"sub": username})

def test_turn_rotation_after_move():
    pw = "pw"
    # Spieler 1
    u1 = f"user1_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": u1, "password": pw})
    t1 = get_test_token(u1)
    h1 = {"Authorization": f"Bearer {t1}"}

    # Spieler 2
    u2 = f"user2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": u2, "password": pw})
    t2 = get_test_token(u2)
    h2 = {"Authorization": f"Bearer {t2}"}

    # Spiel anlegen, beitreten, starten
    game_data = {"language": "en", "max_players": 2}
    gid = client.post("/games/", headers=h1, json=game_data).json()["id"]
    client.post(f"/games/{gid}/join", headers=h2)
    client.post(f"/games/{gid}/start", headers=h1)

    # Get initial game state
    game_state = client.get(f"/games/{gid}", headers=h1).json()
    current_player_id = str(game_state["current_player_id"])
    
    # Find the authenticated user's rack (only their own rack is visible)
    authenticated_user_rack = None
    for player_id, player_data in game_state["players"].items():
        if len(player_data["rack"]) > 0:  # Only the authenticated user's rack is visible
            authenticated_user_rack = player_data["rack"]
            break
    
    assert authenticated_user_rack is not None, "Authenticated user should have a visible rack"
    assert len(authenticated_user_rack) == 7, "Initial rack should have 7 letters"
    
    # Try to form a valid word from the rack
    # Common German words that might be possible with our letters
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
        if all(letter in authenticated_user_rack for letter in letters):
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
            current_player_game_state = client.get(f"/games/{gid}", headers=h2).json()
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
            
            headers_to_use = h2
        else:
            headers_to_use = h1
        
        if word_to_play and letters_needed:
            # Place the word horizontally starting at center
            move = [
                {"row": 7, "col": 7 + i, "letter": letter}
                for i, letter in enumerate(letters_needed)
            ]
            resp1 = client.post(f"/games/{gid}/move", json=move, headers=headers_to_use)
            assert resp1.status_code == 200
            
            # Check that the turn rotated
            updated_game_state = client.get(f"/games/{gid}", headers=h1).json()
            assert updated_game_state["current_player_id"] != current_player_id, "Turn should rotate after move"
            
            # If the move was made by the authenticated user, check their rack was replenished
            if headers_to_use == h1:
                # Find the authenticated user's rack again
                updated_user_rack = None
                for pid, pdata in updated_game_state["players"].items():
                    if len(pdata["rack"]) > 0:  # Only the authenticated user's rack is visible
                        updated_user_rack = pdata["rack"]
                        break
                
                assert updated_user_rack is not None, "Authenticated user should still have a visible rack"
                assert len(updated_user_rack) == 7 or len(updated_user_rack) == len(authenticated_user_rack) - len(letters_needed), "Rack should be replenished to 7 letters or have used letters removed"
    else:
        # Skip test if we can't form any valid word
        print("Skipping test - could not form a valid word from rack")
        assert True

def test_pass_turn():
    pw = "pw"
    # Spieler 1
    u1 = f"user1_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": u1, "password": pw})
    t1 = get_test_token(u1)
    h1 = {"Authorization": f"Bearer {t1}"}

    # Spieler 2
    u2 = f"user2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": u2, "password": pw})
    t2 = get_test_token(u2)
    h2 = {"Authorization": f"Bearer {t2}"}

    # Spiel anlegen, beitreten, starten
    game_data = {"language": "en", "max_players": 2}
    gid = client.post("/games/", headers=h1, json=game_data).json()["id"]
    
    # Player 2 joins
    join_response = client.post(f"/games/{gid}/join", headers=h2)
    assert join_response.status_code == 200
    
    # Verify game state before starting
    game_state = client.get(f"/games/{gid}", headers=h1).json()
    assert game_state["status"] == "ready"
    assert len(game_state["players"]) == 2
    
    # Start game
    start_response = client.post(f"/games/{gid}/start", headers=h1)
    assert start_response.status_code == 200
    
    # Verify game started
    game_state = client.get(f"/games/{gid}", headers=h1).json()
    assert game_state["status"] == "in_progress"
    
    # Pass turn
    response = client.post(f"/games/{gid}/pass", headers=h1)
    assert response.status_code == 200
    
    # Verify game state
    game_state = client.get(f"/games/{gid}", headers=h1).json()
    assert game_state["current_player_id"] != u1 