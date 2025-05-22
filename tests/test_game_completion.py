from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import User, Game, Player, Move
import uuid
import json
from datetime import datetime, timedelta

client = TestClient(app)

def test_manual_game_completion():
    """Test manually completing a game."""
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create two users
        username1 = f"complete_test1_{uuid.uuid4().hex[:6]}"
        username2 = f"complete_test2_{uuid.uuid4().hex[:6]}"
        password = "testpass"
        
        client.post("/users/register", json={"username": username1, "password": password})
        client.post("/users/register", json={"username": username2, "password": password})
        
        token1 = client.post("/auth/token", data={"username": username1, "password": password}).json()["access_token"]
        token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create a game and join
        game_id = client.post("/games/").json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers1)
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers1)
        
        # Make a move
        move = [
            {"row": 7, "col": 7, "letter": "H"},
            {"row": 7, "col": 8, "letter": "A"},
            {"row": 7, "col": 9, "letter": "L"},
            {"row": 7, "col": 10, "letter": "L"},
            {"row": 7, "col": 11, "letter": "O"}
        ]
        
        client.post(
            f"/games/{game_id}/move",
            json={"move_data": move},
            headers=headers1
        )
        
        # Complete the game
        complete_response = client.post(f"/games/{game_id}/complete", headers=headers1)
        assert complete_response.status_code == 200
        assert "completion_data" in complete_response.json()
        
        # Verify game state is updated
        game = db.query(Game).filter(Game.id == game_id).first()
        game_state = json.loads(game.state)
        assert isinstance(game_state, dict)
        assert game_state.get("completed") is True
        assert "completion_data" in game_state
        assert game.current_player_id is None
    
    finally:
        db.close()

def test_game_completion_empty_rack():
    """Test game completion when a player has an empty rack."""
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create two users
        username1 = f"empty_rack1_{uuid.uuid4().hex[:6]}"
        username2 = f"empty_rack2_{uuid.uuid4().hex[:6]}"
        password = "testpass"
        
        client.post("/users/register", json={"username": username1, "password": password})
        client.post("/users/register", json={"username": username2, "password": password})
        
        token1 = client.post("/auth/token", data={"username": username1, "password": password}).json()["access_token"]
        token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create a game and join
        game_id = client.post("/games/").json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers1)
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers1)
        
        # Get user IDs
        user1 = db.query(User).filter(User.username == username1).first()
        
        # Manually set player's rack to empty
        player1 = db.query(Player).filter_by(game_id=game_id, user_id=user1.id).first()
        player1.rack = ""
        db.commit()
        
        # Check game completion
        from app.game_logic.game_completion import check_game_completion
        is_complete, completion_data = check_game_completion(game_id, db)
        
        assert is_complete is True
        assert completion_data["reason"] == "player_empty_rack"
        assert completion_data["winner_id"] == user1.id
    
    finally:
        db.close()

def test_game_completion_consecutive_passes():
    """Test game completion after consecutive passes."""
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create two users
        username1 = f"pass_test1_{uuid.uuid4().hex[:6]}"
        username2 = f"pass_test2_{uuid.uuid4().hex[:6]}"
        password = "testpass"
        
        client.post("/users/register", json={"username": username1, "password": password})
        client.post("/users/register", json={"username": username2, "password": password})
        
        token1 = client.post("/auth/token", data={"username": username1, "password": password}).json()["access_token"]
        token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create a game and join
        game_id = client.post("/games/").json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers1)
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers1)
        
        # Make a move to set scores
        move = [
            {"row": 7, "col": 7, "letter": "H"},
            {"row": 7, "col": 8, "letter": "A"},
            {"row": 7, "col": 9, "letter": "L"},
            {"row": 7, "col": 10, "letter": "L"},
            {"row": 7, "col": 11, "letter": "O"}
        ]
        
        client.post(
            f"/games/{game_id}/move",
            json={"move_data": move},
            headers=headers1
        )
        
        # Create 6 pass moves (3 for each player)
        for _ in range(3):
            # Player 2 passes
            pass_response = client.post(f"/games/{game_id}/pass", headers=headers2)
            assert pass_response.status_code == 200
            
            # Player 1 passes
            pass_response = client.post(f"/games/{game_id}/pass", headers=headers1)
            assert pass_response.status_code == 200
        
        # Check if the last pass triggered game completion
        from app.game_logic.game_completion import check_game_completion
        is_complete, completion_data = check_game_completion(game_id, db)
        
        assert is_complete is True
        assert completion_data["reason"] == "consecutive_passes"
    
    finally:
        db.close()

def test_game_completion_inactivity():
    """Test game completion due to inactivity."""
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create two users
        username1 = f"inactive1_{uuid.uuid4().hex[:6]}"
        username2 = f"inactive2_{uuid.uuid4().hex[:6]}"
        password = "testpass"
        
        client.post("/users/register", json={"username": username1, "password": password})
        client.post("/users/register", json={"username": username2, "password": password})
        
        token1 = client.post("/auth/token", data={"username": username1, "password": password}).json()["access_token"]
        token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create a game and join
        game_id = client.post("/games/").json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers1)
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers1)
        
        # Make a move
        move = [
            {"row": 7, "col": 7, "letter": "H"},
            {"row": 7, "col": 8, "letter": "A"},
            {"row": 7, "col": 9, "letter": "L"},
            {"row": 7, "col": 10, "letter": "L"},
            {"row": 7, "col": 11, "letter": "O"}
        ]
        
        move_response = client.post(
            f"/games/{game_id}/move",
            json={"move_data": move},
            headers=headers1
        )
        
        # Manually update the timestamp of the last move to be 8 days ago
        last_move = db.query(Move).filter(Move.game_id == game_id).first()
        last_move.timestamp = datetime.utcnow() - timedelta(days=8)
        db.commit()
        
        # Check game completion
        from app.game_logic.game_completion import check_game_completion
        is_complete, completion_data = check_game_completion(game_id, db)
        
        assert is_complete is True
        assert completion_data["reason"] == "inactivity"
    
    finally:
        db.close()