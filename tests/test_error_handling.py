from tests.test_utils import get_test_token
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
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with non-existent game ID
    non_existent_id = f"nonexistent_{uuid.uuid4().hex}"
    
    # Try to get game
    response = client.get(f"/games/{non_existent_id}", headers=headers)
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
        json=move,
        headers=headers
    )
    assert response.status_code == 404

def test_invalid_move_data():
    """Test error handling for invalid move data."""
    
    # Create a user and game
    username = f"move_error_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    user1_response = client.post("/users/register", json={"username": username, "password": password})
    assert user1_response.status_code == 200
    test_user_id = user1_response.json()["id"]
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create game with auth
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers, json=game_data)
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]

    # Create second player
    username2 = f"move_error2_{uuid.uuid4().hex[:6]}"
    user2_response = client.post("/users/register", json={"username": username2, "password": password})
    assert user2_response.status_code == 200
    test_user2_id = user2_response.json()["id"]
    token2 = get_test_token(username2)
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Second player joins
    join_response = client.post(f"/games/{game_id}/join", headers=headers2)
    assert join_response.status_code == 200
    
    # Start game
    start_response = client.post(f"/games/{game_id}/start", headers=headers)
    assert start_response.status_code == 200
    
    # Get game state to see who the current player is
    game_response = client.get(f"/games/{game_id}", headers=headers)
    assert game_response.status_code == 200
    game_state = game_response.json()
    current_player_id = game_state["current_player_id"]
    
    # Use the correct player's headers based on who the current player is
    if current_player_id == test_user_id:
        current_headers = headers
    else:
        current_headers = headers2
    
    # Test with empty move data
    response = client.post(
        f"/games/{game_id}/move",
        json=[],
        headers=current_headers
    )
    assert response.status_code == 400, "Empty move data should be rejected with validation error"
    
    # Test with invalid coordinates
    response = client.post(
        f"/games/{game_id}/move",
        json=[{"row": -1, "col": 7, "letter": "A"}],
        headers=current_headers
    )
    assert response.status_code == 400, "Invalid coordinates should be rejected"
    
    # Test with missing required field
    response = client.post(
        f"/games/{game_id}/move",
        json=[{"row": 7, "letter": "A"}],  # Missing 'col'
        headers=current_headers
    )
    assert response.status_code == 400, "Missing required field should cause validation error"
    
    # Test with invalid move format (non-list)
    response = client.post(
        f"/games/{game_id}/move",
        json="not a list",
        headers=current_headers
    )
    assert response.status_code == 422, "Non-list move data should cause validation error"

def test_unauthorized_access():
    """Test error handling for unauthorized access."""
    
    # Try to create a game without auth
    response = client.post("/games/")
    assert response.status_code == 401, "Creating game without auth should return 401"

    # Create an authorized user to create a game
    username = f"auth_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a game properly
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers, json=game_data)
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]

    # Try unauthorized access to various endpoints
    unauthorized_tests = [
        ("GET", f"/games/{game_id}"),
        ("POST", f"/games/{game_id}/join"),
        ("POST", f"/games/{game_id}/start"),
        ("POST", f"/games/{game_id}/move"),
        ("GET", f"/rack/{game_id}")
    ]

    for method, endpoint in unauthorized_tests:
        if method == "GET":
            response = client.get(endpoint)
        else:
            response = client.post(endpoint)
        assert response.status_code == 401, f"{method} {endpoint} without auth should return 401"

    # Try with invalid token
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    for method, endpoint in unauthorized_tests:
        if method == "GET":
            response = client.get(endpoint, headers=invalid_headers)
        else:
            response = client.post(endpoint, headers=invalid_headers)
        assert response.status_code == 401, f"{method} {endpoint} with invalid token should return 401"
