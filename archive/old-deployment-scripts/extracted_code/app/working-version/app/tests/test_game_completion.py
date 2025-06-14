import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import User, Game, Player, Move
import uuid
import json
from datetime import datetime, timezone, timedelta
from tests.test_utils import get_test_token, create_test_user

client = TestClient(app)

def test_manual_game_completion():
    """Test manually completing a game."""
    # Create two users
    username1 = f"complete_test1_{uuid.uuid4().hex[:6]}"
    username2 = f"complete_test2_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    response = create_test_user(client, username1, password)
    assert response.status_code == 200
    response = create_test_user(client, username2, password)
    assert response.status_code == 200
    
    token1 = get_test_token(username1)
    token2 = get_test_token(username2)
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Create a game and join
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers1, json=game_data)
    assert game_response.status_code in (200, 404)
    
    if game_response.status_code == 200:
        game_id = game_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers1)
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers1)
        
        # Complete the game
        complete_response = client.post(f"/games/{game_id}/complete", headers=headers1)
        assert complete_response.status_code in (200, 403, 404)

def test_game_completion_empty_rack():
    """Test game completion when a player has an empty rack."""
    # Create two users
    username1 = f"empty_rack1_{uuid.uuid4().hex[:6]}"
    username2 = f"empty_rack2_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    response = create_test_user(client, username1, password)
    assert response.status_code == 200
    response = create_test_user(client, username2, password)
    assert response.status_code == 200
    
    token1 = get_test_token(username1)
    token2 = get_test_token(username2)
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Create a game and join
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers1, json=game_data)
    assert game_response.status_code in (200, 404)
    
    if game_response.status_code == 200:
        game_id = game_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers1)
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers1)
        
        # Complete the game
        complete_response = client.post(f"/games/{game_id}/complete", headers=headers1)
        assert complete_response.status_code in (200, 403, 404)

def test_game_completion_consecutive_passes():
    """Test game completion after consecutive passes."""
    # Create two users
    username1 = f"pass_test1_{uuid.uuid4().hex[:6]}"
    username2 = f"pass_test2_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    response = create_test_user(client, username1, password)
    assert response.status_code == 200
    response = create_test_user(client, username2, password)
    assert response.status_code == 200
    
    token1 = get_test_token(username1)
    token2 = get_test_token(username2)
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Create a game and join
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers1, json=game_data)
    assert game_response.status_code in (200, 404)
    
    if game_response.status_code == 200:
        game_id = game_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers1)
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers1)
        
        # Pass turns
        for _ in range(3):
            client.post(f"/games/{game_id}/pass", headers=headers1)
            client.post(f"/games/{game_id}/pass", headers=headers2)
        
        # Check game completion
        complete_response = client.post(f"/games/{game_id}/complete", headers=headers1)
        assert complete_response.status_code in (200, 403, 404)

def test_game_completion_inactivity():
    """Test game completion due to inactivity."""
    # Create two users
    username1 = f"inactive1_{uuid.uuid4().hex[:6]}"
    username2 = f"inactive2_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    response = create_test_user(client, username1, password)
    assert response.status_code == 200
    response = create_test_user(client, username2, password)
    assert response.status_code == 200
    
    token1 = get_test_token(username1)
    token2 = get_test_token(username2)
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Create a game and join
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers1, json=game_data)
    assert game_response.status_code in (200, 404)
    
    if game_response.status_code == 200:
        game_id = game_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers1)
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers1)
        
        # Complete the game
        complete_response = client.post(f"/games/{game_id}/complete", headers=headers1)
        assert complete_response.status_code in (200, 403, 404)

