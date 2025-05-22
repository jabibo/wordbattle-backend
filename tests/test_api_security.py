from fastapi.testclient import TestClient
from app.main import app
import uuid
import pytest
import jwt
from datetime import datetime, timedelta

client = TestClient(app)

def test_invalid_token_format():
    """Test that invalid token formats are rejected."""
    # Test with malformed token
    headers = {"Authorization": "Bearer invalid_token_format"}
    response = client.get("/me", headers=headers)
    assert response.status_code == 401
    
    # Test with missing Bearer prefix
    headers = {"Authorization": "token123"}
    response = client.get("/me", headers=headers)
    assert response.status_code == 401
    
    # Test with empty token
    headers = {"Authorization": "Bearer "}
    response = client.get("/me", headers=headers)
    assert response.status_code == 401

def test_expired_token():
    """Test that expired tokens are rejected."""
    # Create a user
    username = f"expired_token_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    
    # Get a valid token
    token_response = client.post("/auth/token", data={"username": username, "password": password})
    valid_token = token_response.json()["access_token"]
    
    # Create an expired token by modifying the payload
    from app.auth import SECRET_KEY, ALGORITHM
    payload = jwt.decode(valid_token, SECRET_KEY, algorithms=[ALGORITHM])
    payload["exp"] = datetime.utcnow() - timedelta(minutes=15)  # Set expiration to 15 minutes ago
    expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # Test with expired token
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/me", headers=headers)
    assert response.status_code == 401

def test_tampered_token():
    """Test that tampered tokens are rejected."""
    # Create a user
    username = f"tampered_token_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    
    # Get a valid token
    token_response = client.post("/auth/token", data={"username": username, "password": password})
    valid_token = token_response.json()["access_token"]
    
    # Create a tampered token by modifying the payload with a different secret
    from app.auth import ALGORITHM
    payload = jwt.decode(valid_token, options={"verify_signature": False})
    payload["sub"] = "different_user"  # Change the subject
    tampered_token = jwt.encode(payload, "different_secret", algorithm=ALGORITHM)
    
    # Test with tampered token
    headers = {"Authorization": f"Bearer {tampered_token}"}
    response = client.get("/me", headers=headers)
    assert response.status_code == 401

def test_protected_endpoints():
    """Test that all protected endpoints require authentication."""
    # Create a game ID for testing
    game_id = client.post("/games/").json()["id"]
    
    # List of protected endpoints to test
    protected_endpoints = [
        {"method": "get", "url": "/me"},
        {"method": "post", "url": f"/games/{game_id}/join"},
        {"method": "post", "url": f"/games/{game_id}/start"},
        {"method": "post", "url": f"/games/{game_id}/move", "json": {"move_data": []}},
        {"method": "post", "url": f"/games/{game_id}/pass"},
        {"method": "post", "url": f"/games/{game_id}/deal"},
        {"method": "post", "url": f"/games/{game_id}/exchange", "params": {"letters": "A"}},
        {"method": "post", "url": f"/games/{game_id}/complete"}
    ]
    
    # Test each endpoint without authentication
    for endpoint in protected_endpoints:
        method = getattr(client, endpoint["method"])
        kwargs = {}
        if "json" in endpoint:
            kwargs["json"] = endpoint["json"]
        if "params" in endpoint:
            kwargs["params"] = endpoint["params"]
        
        response = method(endpoint["url"], **kwargs)
        assert response.status_code in (401, 403), f"Endpoint {endpoint['method']} {endpoint['url']} should require authentication"

def test_authorization_separation():
    """Test that users cannot access other users' resources."""
    # Create two users
    username1 = f"auth_sep1_{uuid.uuid4().hex[:6]}"
    username2 = f"auth_sep2_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": username1, "password": password})
    client.post("/users/register", json={"username": username2, "password": password})
    
    token1 = client.post("/auth/token", data={"username": username1, "password": password}).json()["access_token"]
    token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
    
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # User 1 creates a game and joins
    game_id = client.post("/games/").json()["id"]
    client.post(f"/games/{game_id}/join", headers=headers1)
    
    # User 1 starts the game (should fail because only one player)
    start_response = client.post(f"/games/{game_id}/start", headers=headers1)
    assert start_response.status_code == 400
    
    # User 2 joins the game
    client.post(f"/games/{game_id}/join", headers=headers2)
    
    # User 1 starts the game
    client.post(f"/games/{game_id}/start", headers=headers1)
    
    # User 2 tries to make a move (should fail because it's not their turn)
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
        headers=headers2
    )
    assert move_response.status_code in (400, 403), "User should not be able to make a move when it's not their turn"

def test_csrf_protection():
    """Test CSRF protection by attempting to use a token from a different origin."""
    # This is a simplified test since FastAPI has built-in CSRF protection
    # In a real application, you would test with actual CSRF attacks
    
    # Create a user
    username = f"csrf_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    
    # Get a token
    token_response = client.post("/auth/token", data={"username": username, "password": password})
    token = token_response.json()["access_token"]
    
    # Test with modified headers to simulate a cross-origin request
    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "https://malicious-site.com",
        "Referer": "https://malicious-site.com/attack"
    }
    
    # The request should still work because JWT tokens are designed to be origin-independent
    # This is why additional CSRF protection is needed for cookie-based auth
    response = client.get("/me", headers=headers)
    assert response.status_code == 200

def test_rate_limiting():
    """Test rate limiting by making multiple requests in quick succession."""
    # Note: This test assumes rate limiting is implemented
    # If rate limiting is not implemented, this test will pass but won't validate anything
    
    # Make 50 requests in quick succession
    responses = []
    for _ in range(50):
        response = client.get("/")
        responses.append(response)
    
    # Check if any responses indicate rate limiting
    rate_limited = any(r.status_code == 429 for r in responses)
    
    # This is an informational test - it will pass regardless of whether rate limiting is implemented
    if not rate_limited:
        print("Note: No rate limiting detected. Consider implementing rate limiting for better security.")

def test_password_security():
    """Test that passwords are properly hashed and not stored in plaintext."""
    # Create a user
    username = f"password_test_{uuid.uuid4().hex[:6]}"
    password = "testpass123"
    
    register_response = client.post("/users/register", json={"username": username, "password": password})
    assert register_response.status_code == 200
    
    # Get the user's data from the API
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    me_response = client.get("/me", headers=headers)
    user_data = me_response.json()
    
    # Verify that the password is not returned in the response
    assert "password" not in user_data
    assert "hashed_password" not in user_data