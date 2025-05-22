from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import User, Game, Player, Move
import uuid
import json
import pytest

client = TestClient(app)

@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_user_persistence(db_session):
    """Test that user data is properly persisted in the database."""
    # Create a unique username
    username = f"db_user_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    # Register via API
    response = client.post("/users/register", json={"username": username, "password": password})
    assert response.status_code == 200
    
    # Verify user exists in database
    db_user = db_session.query(User).filter(User.username == username).first()
    assert db_user is not None
    assert db_user.username == username
    assert db_user.hashed_password != password  # Password should be hashed

def test_game_creation_and_persistence(db_session):
    """Test that game data is properly created and persisted."""
    # Create a game via API
    response = client.post("/games/")
    assert response.status_code == 200
    game_id = response.json()["id"]
    
    # Verify game exists in database
    db_game = db_session.query(Game).filter(Game.id == game_id).first()
    assert db_game is not None
    assert db_game.id == game_id
    
    # Verify game state is properly initialized
    game_state = json.loads(db_game.state)
    assert len(game_state) == 15
    assert len(game_state[0]) == 15
    assert all(cell is None for row in game_state for cell in row)

def test_player_join_and_rack_persistence(db_session):
    """Test that player data and rack are properly persisted when joining a game."""
    # Create a user
    username = f"rack_db_user_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a game and join
    game_id = client.post("/games/").json()["id"]
    join_response = client.post(f"/games/{game_id}/join", headers=headers)
    assert join_response.status_code == 200
    initial_rack = join_response.json()["rack"]
    
    # Verify player and rack in database
    db_player = db_session.query(Player).filter_by(game_id=game_id).first()
    assert db_player is not None
    assert db_player.rack == initial_rack
    assert db_player.score == 0
    
    # Get user ID from database
    db_user = db_session.query(User).filter(User.username == username).first()
    assert db_player.user_id == db_user.id

def test_move_persistence(db_session):
    """Test that moves are properly persisted in the database."""
    # Create a user
    username = f"move_db_user_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a second user
    username2 = f"move_db_user2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": username2, "password": password})
    token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Create a game, join and start
    game_id = client.post("/games/").json()["id"]
    client.post(f"/games/{game_id}/join", headers=headers)
    client.post(f"/games/{game_id}/join", headers=headers2)
    client.post(f"/games/{game_id}/start", headers=headers)
    
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
    
    # Verify move in database
    db_move = db_session.query(Move).filter_by(game_id=game_id).first()
    assert db_move is not None
    
    # Verify move data
    move_data = json.loads(db_move.move_data)
    assert len(move_data) == 5
    assert move_data[0]["row"] == 7
    assert move_data[0]["col"] == 7
    assert move_data[0]["letter"] == "H"
    
    # Verify game state was updated
    db_game = db_session.query(Game).filter(Game.id == game_id).first()
    game_state = json.loads(db_game.state)
    assert game_state[7][7] == "H"
    assert game_state[7][8] == "A"
    assert game_state[7][9] == "L"
    assert game_state[7][10] == "L"
    assert game_state[7][11] == "O"
    
    # Verify player turn changed
    assert db_game.current_player_id is not None
    db_user = db_session.query(User).filter(User.username == username).first()
    assert db_game.current_player_id != db_user.id

def test_rack_update_after_move(db_session):
    """Test that player's rack is properly updated after making a move."""
    # Create a user
    username = f"rack_update_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a second user
    username2 = f"rack_update2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": username2, "password": password})
    token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Create a game, join and start
    game_id = client.post("/games/").json()["id"]
    join_response = client.post(f"/games/{game_id}/join", headers=headers)
    initial_rack = join_response.json()["rack"]
    client.post(f"/games/{game_id}/join", headers=headers2)
    client.post(f"/games/{game_id}/start", headers=headers)
    
    # Get user ID from database
    db_user = db_session.query(User).filter(User.username == username).first()
    
    # Manually update player's rack to ensure we have the right letters for the test
    db_player = db_session.query(Player).filter_by(game_id=game_id, user_id=db_user.id).first()
    db_player.rack = "HALLOTE"
    db_session.commit()
    
    # Make a move
    move = [
        {"row": 7, "col": 7, "letter": "H"},
        {"row": 7, "col": 8, "letter": "A"},
        {"row": 7, "col": 9, "letter": "L"},
        {"row": 7, "col": 10, "letter": "L"}
    ]
    
    move_response = client.post(
        f"/games/{game_id}/move",
        json={"move_data": move},
        headers=headers
    )
    assert move_response.status_code == 200
    
    # Verify rack was updated in database
    db_player = db_session.query(Player).filter_by(game_id=game_id, user_id=db_user.id).first()
    assert len(db_player.rack) == 3  # Should have "OTE" left
    assert "O" in db_player.rack
    assert "T" in db_player.rack
    assert "E" in db_player.rack
    assert "H" not in db_player.rack
    assert "A" not in db_player.rack
    assert "L" not in db_player.rack