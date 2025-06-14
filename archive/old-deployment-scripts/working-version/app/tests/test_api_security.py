import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
import jwt
from datetime import datetime, timedelta
from tests.test_utils import get_test_token, create_test_user

client = TestClient(app)

def test_expired_token():
    """Test that expired tokens are rejected."""
    username = f"expired_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    # Register user
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    
    # Use expired token
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}expired"}
    
    # Test with expired token - should be 401 Unauthorized
    response = client.get("/me", headers=headers)
    assert response.status_code == 401

def test_tampered_token():
    """Test that tampered tokens are rejected."""
    username = f"tampered_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    # Register user
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    
    # Use tampered token
    token = get_test_token(username)
    tampered_token = token + "tampered"
    headers = {"Authorization": f"Bearer {tampered_token}"}
    
    # Test with tampered token - should be 401 Unauthorized
    response = client.get("/me", headers=headers)
    assert response.status_code == 401

def test_authorization_separation():
    """Test that users can only access their own data."""
    username1 = f"auth1_{uuid.uuid4().hex[:6]}"
    username2 = f"auth2_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    # Register users
    response = create_test_user(client, username1, password)
    assert response.status_code == 200
    response = create_test_user(client, username2, password)
    assert response.status_code == 200
    
    # Get token for user1
    token1 = get_test_token(username1)
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    # Create a game as user1
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers1, json=game_data)
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]
    
    # Join the game as user1
    client.post(f"/games/{game_id}/join", headers=headers1)
    
    # Try to access user1's profile as user2 - should be 401 or 403
    token2 = get_test_token(username2)
    headers2 = {"Authorization": f"Bearer {token2}"}
    response = client.get(f"/users/{username1}/profile", headers=headers2)
    assert response.status_code in (401, 403, 404)

def test_protected_endpoint_access():
    """Test that protected endpoints require authentication."""
    # Try to access protected endpoint without auth
    response = client.get("/me")
    assert response.status_code == 401
    
    # Create user and get token
    username = f"protected_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Access with token should work
    response = client.get("/me", headers=headers)
    assert response.status_code == 200

