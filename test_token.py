import requests
import json
import uuid

def test_registration_and_authentication():
    """Test the complete registration and authentication flow."""
    base_url = "http://localhost:8000"
    
    # Generate a unique username
    username = f"user_{uuid.uuid4().hex[:8]}"
    password = "testpassword"
    
    print(f"Testing with username: {username}")
    
    # Step 1: Register a new user
    register_url = f"{base_url}/users/register"
    register_data = {"username": username, "password": password}
    register_headers = {"Content-Type": "application/json"}
    
    register_response = requests.post(
        register_url, 
        data=json.dumps(register_data), 
        headers=register_headers
    )
    
    print(f"\n1. Registration Status: {register_response.status_code}")
    print(f"Registration Response: {register_response.text}")
    
    if register_response.status_code != 200:
        print("Registration failed, exiting test")
        return
    
    # Step 2: Get authentication token
    token_url = f"{base_url}/auth/token"
    token_data = {"username": username, "password": password}
    
    token_response = requests.post(token_url, data=token_data)
    
    print(f"\n2. Token Status: {token_response.status_code}")
    print(f"Token Response: {token_response.text}")
    
    if token_response.status_code != 200 or "access_token" not in token_response.json():
        print("Token acquisition failed, exiting test")
        return
    
    token = token_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    
    # Step 3: Access protected endpoint
    me_url = f"{base_url}/me"
    me_response = requests.get(me_url, headers=auth_headers)
    
    print(f"\n3. Protected Endpoint Status: {me_response.status_code}")
    print(f"Protected Endpoint Response: {me_response.text}")
    
    # Step 4: Create a game
    game_url = f"{base_url}/games/"
    game_response = requests.post(game_url, headers=auth_headers)
    
    print(f"\n4. Create Game Status: {game_response.status_code}")
    print(f"Create Game Response: {game_response.text}")
    
    if game_response.status_code != 200 or "id" not in game_response.json():
        print("Game creation failed, exiting test")
        return
    
    game_id = game_response.json()["id"]
    
    # Step 5: Join the game
    join_url = f"{base_url}/games/{game_id}/join"
    join_response = requests.post(join_url, headers=auth_headers)
    
    print(f"\n5. Join Game Status: {join_response.status_code}")
    print(f"Join Game Response: {join_response.text}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_registration_and_authentication()
