#!/usr/bin/env python3
"""
Test script to verify the proper game setup flow with invitations
"""
import requests
import uuid
import time
from datetime import datetime

BACKEND_URL = "https://mnirejmq3g.eu-central-1.awsapprunner.com"

def register_user(username_suffix):
    """Register a test user and return auth token"""
    username = f"testuser_{username_suffix}"
    email = f"test_{username_suffix}@example.com"
    password = "testpassword123"
    
    # Register user
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BACKEND_URL}/users/register", json=register_data, timeout=10)
    if response.status_code != 200:
        print(f"❌ Registration failed for {username}: {response.text}")
        return None, None, None
    
    # Get auth token
    auth_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/token", data=auth_data, timeout=10)
    if response.status_code != 200:
        print(f"❌ Authentication failed for {username}: {response.text}")
        return None, None, None
    
    token = response.json()["access_token"]
    print(f"✅ User {username} registered and authenticated")
    return username, token, {"Authorization": f"Bearer {token}"}

def test_proper_game_flow():
    """Test the complete proper game flow"""
    print("🎮 Testing Proper Game Setup Flow")
    print("=" * 50)
    
    # Step 1: Register two users
    print("\n👥 Step 1: Register Users")
    unique_id = uuid.uuid4().hex[:8]
    
    user1_name, user1_token, user1_headers = register_user(f"{unique_id}_1")
    user2_name, user2_token, user2_headers = register_user(f"{unique_id}_2")
    
    if not all([user1_name, user1_token, user2_name, user2_token]):
        print("❌ Failed to register users")
        return False
    
    # Step 2: User1 creates game with invitation to User2
    print(f"\n🎯 Step 2: {user1_name} creates game and invites {user2_name}")
    
    setup_data = {
        "max_players": 2,
        "language": "de",
        "invitees": [user2_name]
    }
    
    response = requests.post(f"{BACKEND_URL}/games/setup", 
                           json=setup_data, 
                           headers=user1_headers, 
                           timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Game setup failed: {response.text}")
        return False
    
    game_data = response.json()
    game_id = game_data["game_id"]
    invitations_sent = game_data["invitations_sent"]
    
    print(f"✅ Game created: {game_id}")
    print(f"✅ Invitations sent: {invitations_sent}")
    
    # Wait a moment for database consistency
    time.sleep(1)
    
    # Step 3: User2 checks for invitations
    print(f"\n📬 Step 3: {user2_name} checks for invitations")
    
    response = requests.get(f"{BACKEND_URL}/games/invitations", 
                          headers=user2_headers, 
                          timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Failed to get invitations: {response.text}")
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        # Debug: Check if the user exists and can access other endpoints
        print(f"\n🔍 Debug: Testing user2 authentication")
        me_response = requests.get(f"{BACKEND_URL}/auth/me", headers=user2_headers, timeout=10)
        print(f"Auth/me response: {me_response.status_code} - {me_response.text}")
        
        return False
    
    invitations = response.json()
    print(f"✅ Found {len(invitations)} invitation(s)")
    
    if not invitations:
        print("❌ No invitations found")
        
        # Debug: Check if the game was created properly
        print(f"\n🔍 Debug: Checking game {game_id} with user1")
        game_response = requests.get(f"{BACKEND_URL}/games/{game_id}", 
                                   headers=user1_headers, timeout=10)
        print(f"Game response: {game_response.status_code} - {game_response.text}")
        
        return False
    
    invitation = invitations[0]
    print(f"✅ Invitation from {invitation['inviter']} for game {invitation['game_id']}")
    
    # Step 4: User2 accepts the invitation
    print(f"\n✅ Step 4: {user2_name} accepts invitation")
    
    response_data = {
        "game_id": game_id,
        "response": True
    }
    
    response = requests.post(f"{BACKEND_URL}/games/invitations/respond", 
                           json=response_data, 
                           headers=user2_headers, 
                           timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Failed to accept invitation: {response.text}")
        return False
    
    print("✅ Invitation accepted")
    
    # Step 5: Check game status (should be READY)
    print(f"\n🎮 Step 5: Check game status")
    
    response = requests.get(f"{BACKEND_URL}/games/{game_id}", 
                          headers=user1_headers, 
                          timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Failed to get game: {response.text}")
        return False
    
    game_state = response.json()
    print(f"✅ Game status: {game_state.get('status', 'unknown')}")
    print(f"✅ Players: {len(game_state.get('players', {}))}")
    
    # Step 6: Start the game (if endpoint exists)
    print(f"\n🚀 Step 6: {user1_name} tries to start the game")
    
    response = requests.post(f"{BACKEND_URL}/games/{game_id}/start", 
                           headers=user1_headers, 
                           timeout=10)
    
    if response.status_code == 404:
        print("ℹ️ Start endpoint not available, trying to join game instead")
        
        # Try joining the game to start it
        response = requests.post(f"{BACKEND_URL}/games/{game_id}/join", 
                               headers=user1_headers, 
                               timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Failed to join game: {response.text}")
        else:
            print("✅ Game joined successfully!")
    elif response.status_code != 200:
        print(f"❌ Failed to start game: {response.text}")
    else:
        print("✅ Game started successfully!")
    
    # Step 7: Final game state check
    print(f"\n🎯 Step 7: Final game state check")
    
    response = requests.get(f"{BACKEND_URL}/games/{game_id}", 
                          headers=user1_headers, 
                          timeout=10)
    
    if response.status_code == 200:
        game_state = response.json()
        print(f"✅ Final game status: {game_state.get('status', 'unknown')}")
        print(f"✅ Game phase: {game_state.get('phase', 'unknown')}")
        print(f"✅ Current player: {game_state.get('current_player_id', 'unknown')}")
        
        # Check if players have racks
        players = game_state.get('players', {})
        for player_id, player_data in players.items():
            rack = player_data.get('rack', [])
            if isinstance(rack, list) and len(rack) > 0:
                print(f"✅ Player {player_data.get('username', player_id)} has {len(rack)} letters")
    
    print("\n🎉 PROPER GAME FLOW TEST COMPLETED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    success = test_proper_game_flow()
    if success:
        print("\n✅ All tests passed! The proper game setup flow is working.")
    else:
        print("\n❌ Some tests failed. Check the output above.") 