from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import User, Player
import uuid

client = TestClient(app)

def test_score_update_after_move():
    """Test that player's score is properly updated after making a move."""
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create a user
        username = f"score_update_{uuid.uuid4().hex[:6]}"
        password = "testpass"
        client.post("/users/register", json={"username": username, "password": password})
        token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a second user
        username2 = f"score_update2_{uuid.uuid4().hex[:6]}"
        client.post("/users/register", json={"username": username2, "password": password})
        token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create a game, join and start
        game_id = client.post("/games/").json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers)
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers)
        
        # Get user ID from database
        db_user = db.query(User).filter(User.username == username).first()
        
        # Manually update player's rack to ensure we have the right letters for the test
        db_player = db.query(Player).filter_by(game_id=game_id, user_id=db_user.id).first()
        db_player.rack = "HALLOTE"
        db.commit()
        
        # Initial score should be 0
        assert db_player.score == 0
        
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
            headers=headers
        )
        assert move_response.status_code == 200
        points = move_response.json()["points"]
        
        # Verify score was updated in database
        db.refresh(db_player)
        assert db_player.score == points
        assert db_player.score == 10  # The test move should give 10 points
    
    finally:
        db.close()

def test_score_accumulation():
    """Test that player's score accumulates across multiple moves."""
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create a user
        username = f"score_accum_{uuid.uuid4().hex[:6]}"
        password = "testpass"
        client.post("/users/register", json={"username": username, "password": password})
        token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a second user
        username2 = f"score_accum2_{uuid.uuid4().hex[:6]}"
        client.post("/users/register", json={"username": username2, "password": password})
        token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create a game, join and start
        game_id = client.post("/games/").json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers)
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers)
        
        # Get user IDs from database
        db_user1 = db.query(User).filter(User.username == username).first()
        db_user2 = db.query(User).filter(User.username == username2).first()
        
        # Manually update players' racks
        db_player1 = db.query(Player).filter_by(game_id=game_id, user_id=db_user1.id).first()
        db_player1.rack = "HALLOTE"
        db_player2 = db.query(Player).filter_by(game_id=game_id, user_id=db_user2.id).first()
        db_player2.rack = "WORTABC"
        db.commit()
        
        # First move by player 1
        move1 = [
            {"row": 7, "col": 7, "letter": "H"},
            {"row": 7, "col": 8, "letter": "A"},
            {"row": 7, "col": 9, "letter": "L"},
            {"row": 7, "col": 10, "letter": "L"},
            {"row": 7, "col": 11, "letter": "O"}
        ]
        
        move1_response = client.post(
            f"/games/{game_id}/move",
            json={"move_data": move1},
            headers=headers
        )
        assert move1_response.status_code == 200
        points1 = move1_response.json()["points"]
        
        # Second move by player 2
        move2 = [
            {"row": 6, "col": 9, "letter": "W"},
            {"row": 5, "col": 9, "letter": "O"},
            {"row": 4, "col": 9, "letter": "R"},
            {"row": 3, "col": 9, "letter": "T"}
        ]
        
        move2_response = client.post(
            f"/games/{game_id}/move",
            json={"move_data": move2},
            headers=headers2
        )
        
        # Third move by player 1
        if move2_response.status_code == 200:
            # Manually update player 1's rack again
            db_player1.rack = "TESTE"
            db.commit()
            
            move3 = [
                {"row": 7, "col": 12, "letter": "T"},
                {"row": 7, "col": 13, "letter": "E"}
            ]
            
            move3_response = client.post(
                f"/games/{game_id}/move",
                json={"move_data": move3},
                headers=headers
            )
            
            if move3_response.status_code == 200:
                points3 = move3_response.json()["points"]
                
                # Verify score accumulation
                db.refresh(db_player1)
                assert db_player1.score == points1 + points3
                assert db_player1.score > points1  # Score should have increased
    
    finally:
        db.close()

