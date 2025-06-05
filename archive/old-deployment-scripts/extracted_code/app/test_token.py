import requests
import json
import uuid
from fastapi.testclient import TestClient
from app.main import app

def test_registration_and_authentication():
    """Test the complete registration and authentication flow."""
    # Use TestClient instead of real HTTP requests
    client = TestClient(app)
    
    # Generate a unique username
    username = f"user_{uuid.uuid4().hex[:8]}"
    password = "testpassword"
    
    print(f"Testing with username: {username}")
    
    # Step 1: Register a new user
    register_data = {"username": username, "password": password}
    register_response = client.post("/users/register", json=register_data)
    
    print(f"\n1. Registration Status: {register_response.status_code}")
    print(f"Registration Response: {register_response.text}")
    
    assert register_response.status_code == 200, "Registration failed"
    
    # Step 2: Get authentication token
    token_data = {"username": username, "password": password}
    token_response = client.post("/auth/token", data=token_data)
    
    print(f"\n2. Token Status: {token_response.status_code}")
    print(f"Token Response: {token_response.text}")
    
    assert token_response.status_code == 200, "Token acquisition failed"
    assert "access_token" in token_response.json(), "No access token in response"
    
    token = token_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    
    # Step 3: Access protected endpoint
    me_response = client.get("/me", headers=auth_headers)
    
    print(f"\n3. Protected Endpoint Status: {me_response.status_code}")
    print(f"Protected Endpoint Response: {me_response.text}")
    
    assert me_response.status_code == 200, "Protected endpoint access failed"
    
    # Step 4: Create a game
    game_data = {
        "language": "en",
        "max_players": 2
    }
    game_response = client.post("/games/", headers=auth_headers, json=game_data)
    
    print(f"\n4. Create Game Status: {game_response.status_code}")
    print(f"Create Game Response: {game_response.text}")
    
    assert game_response.status_code == 200, "Game creation failed"
    game_json = game_response.json()
    assert "id" in game_json, "No game ID in response"
    assert game_json["language"] == "en", "Wrong game language"
    assert game_json["max_players"] == 2, "Wrong max players"
    
    game_id = game_json["id"]
    
    # Step 5: Verify the creator is already a player (no need to join)
    # The creator is automatically added as a player when creating the game
    get_game_response = client.get(f"/games/{game_id}", headers=auth_headers)
    
    print(f"\n5. Get Game Status: {get_game_response.status_code}")
    print(f"Get Game Response: {get_game_response.text}")
    
    assert get_game_response.status_code == 200, "Get game failed"
    game_details = get_game_response.json()
    assert "players" in game_details, "No players info in game response"
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_registration_and_authentication()
