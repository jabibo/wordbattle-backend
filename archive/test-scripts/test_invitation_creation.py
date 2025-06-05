#!/usr/bin/env python3
"""
Test script to debug invitation creation
"""
import requests
import uuid

# Configuration - using Google Cloud Run
BACKEND_URL = "https://wordbattle-backend-skhco4fxoq-ew.a.run.app"

def test_invitation_creation():
    """Test if invitations are actually being created"""
    print("🔍 Testing Invitation Creation")
    print("=" * 40)
    
    unique_id = uuid.uuid4().hex[:6]
    
    # Register two users
    users = []
    for i in [1, 2]:
        username = f"inv_test_{unique_id}_{i}"
        email = f"inv_test_{unique_id}_{i}@example.com"
        password = "testpass123"
        
        # Register
        register_data = {"username": username, "email": email, "password": password}
        response = requests.post(f"{BACKEND_URL}/users/register", json=register_data, timeout=10)
        print(f"Register {username}: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to register {username}")
            return
        
        # Auth
        auth_data = {"username": username, "password": password}
        response = requests.post(f"{BACKEND_URL}/auth/token", data=auth_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Failed to authenticate {username}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        users.append((username, headers))
    
    user1_name, user1_headers = users[0]
    user2_name, user2_headers = users[1]
    
    print(f"\n✅ Both users registered successfully")
    
    # Test 1: Try to create game with non-existent user
    print(f"\n🧪 Test 1: Create game with non-existent invitee")
    setup_data = {
        "max_players": 2,
        "language": "de",
        "invitees": ["nonexistent_user_12345"]
    }
    
    response = requests.post(f"{BACKEND_URL}/games/setup", json=setup_data, headers=user1_headers, timeout=10)
    print(f"Game setup with invalid user: {response.status_code} - {response.text}")
    
    # Test 2: Create game with valid user
    print(f"\n🧪 Test 2: Create game with valid invitee")
    setup_data = {
        "max_players": 2,
        "language": "de",
        "invitees": [user2_name]
    }
    
    response = requests.post(f"{BACKEND_URL}/games/setup", json=setup_data, headers=user1_headers, timeout=10)
    print(f"Game setup with valid user: {response.status_code} - {response.text}")
    
    if response.status_code != 200:
        print("❌ Failed to create game")
        return
    
    game_data = response.json()
    game_id = game_data["game_id"]
    invitations_sent = game_data["invitations_sent"]
    
    print(f"✅ Game created: {game_id}")
    print(f"✅ Invitations sent: {invitations_sent}")
    
    # Test 3: Check if user2 can see the invitation
    print(f"\n🧪 Test 3: Check invitations for user2")
    response = requests.get(f"{BACKEND_URL}/games/invitations", headers=user2_headers, timeout=10)
    print(f"Invitations response: {response.status_code}")
    print(f"Response body: {response.text}")
    print(f"Response headers: {dict(response.headers)}")
    
    # Test 4: Check if user1 can see the game
    print(f"\n🧪 Test 4: Check game details for user1")
    response = requests.get(f"{BACKEND_URL}/games/{game_id}", headers=user1_headers, timeout=10)
    print(f"Game details: {response.status_code}")
    if response.status_code == 200:
        game_data = response.json()
        print(f"Game status: {game_data.get('status')}")
        print(f"Players: {list(game_data.get('players', {}).keys())}")
    
    # Test 5: Try to respond to invitation (even though we can't see it)
    print(f"\n🧪 Test 5: Try to respond to invitation")
    response_data = {
        "game_id": game_id,
        "response": True
    }
    
    response = requests.post(f"{BACKEND_URL}/games/invitations/respond", 
                           json=response_data, 
                           headers=user2_headers, 
                           timeout=10)
    print(f"Invitation response: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_invitation_creation() 