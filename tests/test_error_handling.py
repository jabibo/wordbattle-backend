from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_invalid_game_id():
    """Test error handling for invalid game IDs."""
    
    # Create a user for authentication
    username = f"error_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with non-existent game ID
    non_existent_id = f"nonexistent_{uuid.uuid4().hex}"
    
    # Try to get game
    response = client.get(f"/games/{non_existent_id}")
    assert response.status_code == 404
    
    # Try to join game
    response = client.post(f"/games/{non_existent_id}/join", headers=headers)
    assert response.status_code == 404
    
    # Try to start game
    response = client.post(f"/games/{non_existent_id}/start", headers=headers)
    assert response.status_code == 404
    
    # Try to make a move
    move = [{"row": 7, "col": 7, "letter": "A"}]
    response = client.post(
        f"/games/{non_existent_id}/move",
        json={"move_data": move},
        headers=headers
    )
    assert response.status_code == 404

def test_invalid_move_data():
    """Test error handling for invalid move data."""
    
    # Create a user and game
    username = f"move_error_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    game_id = client.post("/games/").json()["id"]
    client.post(f"/games/{game_id}/join", headers=headers)
    
    # Test with empty move data
    response = client.post(
        f"/games/{game_id}/move",
        json={"move_data": []},
        headers=headers
    )
    assert response.status_code == 400
    
    # Test with invalid coordinates
    response = client.post(
        f"/games/{game_id}/move",
        json={"move_data": [{"row": -1, "col": 7, "letter": "A"}]},
        headers=headers
    )
    assert response.status_code == 400
    
    # Test with missing required field
    response = client.post(
        f"/games/{game_id}/move",
        json={"move_data": [{"row": 7, "letter": "A"}]},  # Missing 'col'
        headers=headers
    )
    assert response.status_code == 422  # Validation error

def test_unauthorized_access():
    """Test error handling for unauthorized access."""
    
    # Create a game
    game_id = client.post("/games/").json()["id"]
    
    # Try to access protected endpoints without authentication
    endpoints = [
        f"/games/{game_id}/join",
        f"/games/{game_id}/start",
        f"/games/{game_id}/move",
        f"/games/{game_id}/pass",
        f"/games/{game_id}/deal",
        f"/games/{game_id}/exchange",
        "/me",
        "/games/mine"
    ]
    
    for endpoint in endpoints:
        response = client.post(endpoint)
        assert response.status_code in (401, 405)  # 401 Unauthorized or 405 Method Not Allowed