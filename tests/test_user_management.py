from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_register_duplicate_username():
    # Create a unique username for this test
    username = f"duplicate_user_{uuid.uuid4().hex[:6]}"
    password = "testpass123"
    
    # First registration should succeed
    response1 = client.post(
        "/users/register", 
        json={"username": username, "password": password}
    )
    assert response1.status_code == 200
    
    # Second registration with same username should fail
    response2 = client.post(
        "/users/register", 
        json={"username": username, "password": password}
    )
    assert response2.status_code == 400
    assert "bereits vergeben" in response2.json().get("detail", "")

def test_login_invalid_credentials():
    # Create a unique username for this test
    username = f"login_test_{uuid.uuid4().hex[:6]}"
    password = "correctpass"
    wrong_password = "wrongpass"
    
    # Register the user
    client.post(
        "/users/register", 
        json={"username": username, "password": password}
    )
    
    # Test with wrong password
    response1 = client.post(
        "/auth/token", 
        data={"username": username, "password": wrong_password}
    )
    assert response1.status_code == 400
    
    # Test with non-existent username
    response2 = client.post(
        "/auth/token", 
        data={"username": f"nonexistent_{uuid.uuid4().hex}", "password": password}
    )
    assert response2.status_code == 400

def test_user_authentication_required():
    # Try to access a protected endpoint without authentication
    response = client.get("/me")
    assert response.status_code == 401
    
    # Try to join a game without authentication
    game_id = client.post("/games/").json()["id"]
    response = client.post(f"/games/{game_id}/join")
    assert response.status_code == 401