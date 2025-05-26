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
    
    # Find the authenticated user's ID (only their own rack is visible)
    authenticated_user_id = None
    for player_id, player_data in game_state["players"].items():
        if len(player_data["rack"]) > 0:  # Only the authenticated user's rack is visible
            authenticated_user_id = player_id
            break
    
    assert authenticated_user_id is not None, "Authenticated user should be found"
    
    # Set a predetermined rack that can form the word "DOG" (D, O, G + extra letters)
    # Update the player's rack directly in the database to ensure we can make a valid move
    from app.database import SessionLocal
    from app.models import Player
    
    db = SessionLocal()
    try:
        player = db.query(Player).filter_by(game_id=gid, user_id=int(authenticated_user_id)).first()
        if player:
            player.rack = "DOGXYZW"  # DOG + 4 extra letters to make 7 total
            db.commit()
    finally:
        db.close()
    
    # Now test word validation with our predetermined rack
    # Get the updated game state to see the rack we just set
    updated_game_state = client.get(f"/games/{gid}", headers=h1).json()
    
    # Find the current player's rack
    current_player_rack = None
    if str(current_player_id) == str(authenticated_user_id):
        # Current player is the authenticated user, we can see their rack
        for pid, pdata in updated_game_state["players"].items():
            if len(pdata["rack"]) > 0:  # This is the authenticated user's rack
                current_player_rack = pdata["rack"]
                break
        headers_to_use = h1
    else:
        # Current player is the other user, need to set their rack too
        db = SessionLocal()
        try:
            other_player = db.query(Player).filter_by(game_id=gid, user_id=int(current_player_id)).first()
            if other_player:
                other_player.rack = "CATXYZW"  # CAT + 4 extra letters
                db.commit()
        finally:
            db.close()
        
        # Get their game state
        current_player_game_state = client.get(f"/games/{gid}", headers=h2).json()
        for pid, pdata in current_player_game_state["players"].items():
            if len(pdata["rack"]) > 0:  # This is the current player's rack
                current_player_rack = pdata["rack"]
                break
        headers_to_use = h2
    
    # Test word validation - try to find a valid word from available letters
    possible_words = [
        ("DOG", ["D", "O", "G"]),
        ("CAT", ["C", "A", "T"]),
        ("GO", ["G", "O"]),
        ("AT", ["A", "T"]),
        ("TO", ["T", "O"])
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
    move = [
        {"row": 7, "col": 7 + i, "letter": letter}
        for i, letter in enumerate(letters_needed)
    ]
    
    # Make the move (this tests the move validation and word checking)
    resp1 = client.post(f"/games/{gid}/move", json=move, headers=headers_to_use)
    assert resp1.status_code == 200, f"Move should succeed for word '{word_to_play}', got {resp1.status_code}: {resp1.json()}"
    
    # Check that the turn rotated (this tests turn management)
    final_game_state = client.get(f"/games/{gid}", headers=h1).json()
    assert final_game_state["current_player_id"] != current_player_id, "Turn should rotate after move"
    
    # Verify the move was recorded and scored properly
    move_response_data = resp1.json()
    assert "points_gained" in move_response_data, "Move response should include points"
    assert move_response_data["points_gained"] > 0, "Should gain points for valid word"

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