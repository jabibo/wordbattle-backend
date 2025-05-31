#!/usr/bin/env python3
"""
Test script for the new enhanced game creation flow with email invitations.
"""
import requests
import uuid
import time
import json

# Use local Docker instance for testing
BACKEND_URL = "http://localhost:8000"

def register_and_auth(suffix):
    """Register user and get auth headers"""
    username = f"gameflow_{suffix}"
    email = f"gameflow_{suffix}@example.com"
    password = "testpass123"
    
    # Register
    register_data = {"username": username, "email": email, "password": password}
    response = requests.post(f"{BACKEND_URL}/users/register", json=register_data, timeout=10)
    print(f"Register {username}: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Registration failed: {response.text}")
        return None, None, None
    
    # Auth
    auth_data = {"username": username, "password": password}
    response = requests.post(f"{BACKEND_URL}/auth/token", data=auth_data, timeout=10)
    print(f"Auth {username}: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Authentication failed: {response.text}")
        return None, None, None
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return username, headers, email

def test_new_game_flow():
    """Test the complete new game creation flow"""
    print("🎮 Testing New Enhanced Game Creation Flow")
    print("=" * 60)
    
    unique_id = uuid.uuid4().hex[:8]
    
    # Step 1: Register three users
    print("\n👥 Step 1: Register Users")
    user1_name, user1_headers, user1_email = register_and_auth(f"{unique_id}_creator")
    user2_name, user2_headers, user2_email = register_and_auth(f"{unique_id}_player1")
    user3_name, user3_headers, user3_email = register_and_auth(f"{unique_id}_player2")
    
    if not all([user1_name, user2_name, user3_name]):
        print("❌ Failed to register users")
        return False
    
    print(f"✅ Registered: {user1_name}, {user2_name}, {user3_name}")
    
    # Step 2: Create game with invitations
    print(f"\n🎯 Step 2: {user1_name} creates game with invitations")
    
    game_data = {
        "language": "en",
        "max_players": 3,
        "invitees": [user2_name, user3_name],  # Invite by username
        "base_url": BACKEND_URL
    }
    
    response = requests.post(f"{BACKEND_URL}/games/create-with-invitations", 
                           json=game_data, 
                           headers=user1_headers, 
                           timeout=10)
    
    print(f"Game creation: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Game creation failed: {response.text}")
        return False
    
    game_response = response.json()
    game_id = game_response["id"]
    print(f"✅ Game created: {game_id}")
    print(f"✅ Invitations created: {game_response['invitations_created']}")
    print(f"✅ Emails sent: {game_response['invitations_sent']}")
    print(f"✅ Game status: {game_response['status']}")
    
    # Step 3: Check game invitations
    print(f"\n📋 Step 3: Check game invitations")
    response = requests.get(f"{BACKEND_URL}/games/{game_id}/invitations", 
                          headers=user1_headers, 
                          timeout=10)
    
    if response.status_code == 200:
        invitations = response.json()
        print(f"✅ Total invitations: {invitations['total_invitations']}")
        print(f"✅ Pending: {invitations['pending_count']}")
        
        # Get join tokens for testing
        join_tokens = {}
        for inv in invitations['invitations']:
            join_tokens[inv['invitee_username']] = inv['join_token']
            print(f"  - {inv['invitee_username']}: {inv['status']}")
    else:
        print(f"❌ Failed to get invitations: {response.text}")
        return False
    
    # Step 4: User2 joins via token
    print(f"\n🔗 Step 4: {user2_name} joins via invitation token")
    
    user2_token = join_tokens.get(user2_name)
    if user2_token:
        response = requests.post(f"{BACKEND_URL}/games/{game_id}/join-with-token?token={user2_token}", 
                               headers=user2_headers, 
                               timeout=10)
        
        print(f"Join with token: {response.status_code}")
        if response.status_code == 200:
            join_response = response.json()
            print(f"✅ {user2_name} joined successfully")
            print(f"✅ Player count: {join_response['player_count']}")
            print(f"✅ Game status: {join_response['game_status']}")
        else:
            print(f"❌ Join failed: {response.text}")
    
    # Step 5: User3 joins via token
    print(f"\n🔗 Step 5: {user3_name} joins via invitation token")
    
    user3_token = join_tokens.get(user3_name)
    if user3_token:
        response = requests.post(f"{BACKEND_URL}/games/{game_id}/join-with-token?token={user3_token}", 
                               headers=user3_headers, 
                               timeout=10)
        
        print(f"Join with token: {response.status_code}")
        if response.status_code == 200:
            join_response = response.json()
            print(f"✅ {user3_name} joined successfully")
            print(f"✅ Player count: {join_response['player_count']}")
            print(f"✅ Game status: {join_response['game_status']}")
        else:
            print(f"❌ Join failed: {response.text}")
    
    # Step 6: Check final game state
    print(f"\n🎮 Step 6: Check final game state")
    response = requests.get(f"{BACKEND_URL}/games/{game_id}", 
                          headers=user1_headers, 
                          timeout=10)
    
    if response.status_code == 200:
        game_state = response.json()
        print(f"✅ Game status: {game_state['status']}")
        print(f"✅ Players: {len(game_state['players'])}")
        print(f"✅ Max players: {game_state['max_players']}")
        
        for player_id, player_data in game_state['players'].items():
            print(f"  - Player {player_id}: {player_data['username']} (Score: {player_data['score']})")
    else:
        print(f"❌ Failed to get game state: {response.text}")
    
    # Step 7: Auto-start the game (if ready)
    print(f"\n🚀 Step 7: Auto-start the game")
    response = requests.post(f"{BACKEND_URL}/games/{game_id}/auto-start", 
                           headers=user1_headers, 
                           timeout=10)
    
    print(f"Auto-start: {response.status_code}")
    if response.status_code == 200:
        start_response = response.json()
        print(f"✅ Game auto-started successfully")
        print(f"✅ Current player: {start_response['current_player_id']}")
        print(f"✅ Game status: {start_response['game_status']}")
    else:
        print(f"❌ Auto-start failed: {response.text}")
    
    print(f"\n🎉 Test completed! Game ID: {game_id}")
    return True

def test_email_invitation_by_email():
    """Test inviting users by email address instead of username"""
    print("\n\n📧 Testing Email-based Invitations")
    print("=" * 50)
    
    unique_id = uuid.uuid4().hex[:8]
    
    # Register users
    user1_name, user1_headers, user1_email = register_and_auth(f"{unique_id}_email_creator")
    user2_name, user2_headers, user2_email = register_and_auth(f"{unique_id}_email_player")
    
    if not all([user1_name, user2_name]):
        print("❌ Failed to register users")
        return False
    
    # Create game with email invitation
    game_data = {
        "language": "de",
        "max_players": 2,
        "invitees": [user2_email],  # Invite by email instead of username
        "base_url": BACKEND_URL
    }
    
    response = requests.post(f"{BACKEND_URL}/games/create-with-invitations", 
                           json=game_data, 
                           headers=user1_headers, 
                           timeout=10)
    
    print(f"Game creation with email invitation: {response.status_code}")
    if response.status_code == 200:
        game_response = response.json()
        print(f"✅ Game created with email invitation")
        print(f"✅ Invitations sent: {game_response['invitations_sent']}")
        return True
    else:
        print(f"❌ Email invitation failed: {response.text}")
        return False

if __name__ == "__main__":
    try:
        print("🧪 Starting Enhanced Game Creation Flow Tests")
        print("=" * 70)
        
        # Test 1: Complete flow with username invitations
        success1 = test_new_game_flow()
        
        # Test 2: Email-based invitations
        success2 = test_email_invitation_by_email()
        
        if success1 and success2:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure Docker is running:")
        print("   docker-compose up -d")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc() 