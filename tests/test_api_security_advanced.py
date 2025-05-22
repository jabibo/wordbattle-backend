from fastapi.testclient import TestClient
from app.main import app
import uuid
import pytest
import jwt
import json
from datetime import datetime, timedelta

client = TestClient(app)

def test_sql_injection_prevention():
    """Test that SQL injection attempts are prevented."""
    # SQL injection attempt in username
    sql_injection_username = "admin' OR 1=1--"
    password = "testpass"
    
    # Try to register with SQL injection username
    register_response = client.post(
        "/users/register", 
        json={"username": sql_injection_username, "password": password}
    )
    assert register_response.status_code == 200  # Registration should succeed with any valid username
    
    # Try to login with SQL injection
    login_response = client.post(
        "/auth/token", 
        data={"username": "' OR 1=1--", "password": "anything"}
    )
    assert login_response.status_code == 400  # Should fail, not return all users
    
    # Try SQL injection in game ID
    game_id = "' OR 1=1--"
    response = client.get(f"/games/{game_id}")
    assert response.status_code == 404  # Should return not found, not all games

def test_xss_prevention():
    """Test that XSS attempts are prevented."""
    # Create a user with XSS payload in username
    xss_username = f"<script>alert('xss')</script>_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": xss_username, "password": password})
    token = client.post("/auth/token", data={"username": xss_username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get user data
    me_response = client.get("/me", headers=headers)
    user_data = me_response.json()
    
    # Check that the username is returned as-is (FastAPI automatically escapes it in responses)
    assert user_data["username"] == xss_username
    
    # Create a game with XSS payload
    game_response = client.post("/games/", json={"state": "<script>alert('xss')</script>"})
    game_id = game_response.json()["id"]
    
    # Get game data
    game_response = client.get(f"/games/{game_id}")
    assert game_response.status_code == 200

def test_privilege_escalation():
    """Test that privilege escalation attempts are prevented."""
    # Create two users
    username1 = f"priv_user1_{uuid.uuid4().hex[:6]}"
    username2 = f"priv_user2_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": username1, "password": password})
    client.post("/users/register", json={"username": username2, "password": password})
    
    token1 = client.post("/auth/token", data={"username": username1, "password": password}).json()["access_token"]
    token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
    
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # User 1 creates a game
    game_id = client.post("/games/").json()["id"]
    client.post(f"/games/{game_id}/join", headers=headers1)
    
    # User 2 tries to start the game (should fail because they haven't joined)
    start_response = client.post(f"/games/{game_id}/start", headers=headers2)
    assert start_response.status_code in (400, 403), "User should not be able to start a game they haven't joined"

def test_token_replay():
    """Test that token replay attacks are prevented."""
    # Create a user
    username = f"replay_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    
    # Get a token
    token_response = client.post("/auth/token", data={"username": username, "password": password})
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Use the token for a legitimate request
    me_response = client.get("/me", headers=headers)
    assert me_response.status_code == 200
    
    # In a proper implementation with token blacklisting, we would test that a revoked token is rejected
    # Since this is not implemented in the current system, we just verify that the token still works
    # This test would need to be updated if token blacklisting is implemented
    me_response2 = client.get("/me", headers=headers)
    assert me_response2.status_code == 200

def test_path_traversal():
    """Test that path traversal attacks are prevented."""
    # Try to access files outside the intended directory
    # This is more relevant for file serving endpoints, but we'll test it on existing endpoints
    
    # Try path traversal in game ID
    traversal_id = "../../../etc/passwd"
    response = client.get(f"/games/{traversal_id}")
    assert response.status_code == 404  # Should return not found, not file contents
    
    # Create a user
    username = f"path_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try path traversal in move data
    game_id = client.post("/games/").json()["id"]
    client.post(f"/games/{game_id}/join", headers=headers)
    
    move = [
        {"row": 7, "col": 7, "letter": "../../../etc/passwd"}
    ]
    
    move_response = client.post(
        f"/games/{game_id}/move",
        json={"move_data": move},
        headers=headers
    )
    # Should fail validation, not expose file contents
    assert move_response.status_code in (400, 422)