#!/usr/bin/env python3

import requests
import json
import time
import random
import string

# Base URL for the deployed service
BASE_URL = "https://wordbattle-backend-441752988736.europe-west1.run.app"

def generate_test_email():
    """Generate a unique test email address."""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

def test_invitation_status_fix():
    """Test that invitation status is correctly updated when someone joins a game."""
    
    print("🧪 Testing Invitation Status Fix")
    print("=" * 50)
    
    # Step 1: Register two test users
    print("\n1. Registering test users...")
    
    user1_email = generate_test_email()
    user1_password = "TestPassword123!"
    user1_username = f"player1_{random.randint(1000, 9999)}"
    
    user2_email = generate_test_email()
    user2_password = "TestPassword123!"
    user2_username = f"player2_{random.randint(1000, 9999)}"
    
    # Register user 1
    user1_reg = requests.post(f"{BASE_URL}/users/register", json={
        "username": user1_username,
        "email": user1_email,
        "password": user1_password
    })
    
    if user1_reg.status_code != 200:
        print(f"   ❌ Failed to register user1: {user1_reg.status_code} {user1_reg.text}")
        return False
    
    # Register user 2
    user2_reg = requests.post(f"{BASE_URL}/users/register", json={
        "username": user2_username,
        "email": user2_email,
        "password": user2_password
    })
    
    if user2_reg.status_code != 200:
        print(f"   ❌ Failed to register user2: {user2_reg.status_code} {user2_reg.text}")
        return False
    
    print(f"   ✅ Registered users: {user1_username} and {user2_username}")
    
    # Step 2: Login both users
    print("\n2. Logging in users...")
    
    # Login user 1
    user1_login = requests.post(f"{BASE_URL}/auth/token", data={
        "username": user1_username,
        "password": user1_password
    })
    
    if user1_login.status_code != 200:
        print(f"   ❌ Failed to login user1: {user1_login.status_code}")
        return False
    
    user1_token = user1_login.json()["access_token"]
    user1_headers = {"Authorization": f"Bearer {user1_token}"}
    
    # Login user 2
    user2_login = requests.post(f"{BASE_URL}/auth/token", data={
        "username": user2_username,
        "password": user2_password
    })
    
    if user2_login.status_code != 200:
        print(f"   ❌ Failed to login user2: {user2_login.status_code}")
        return False
    
    user2_token = user2_login.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    
    print("   ✅ Both users logged in successfully")
    
    # Step 3: User1 creates game with invitation to User2
    print("\n3. Creating game with invitation...")
    
    create_game_response = requests.post(f"{BASE_URL}/games/create-with-invitations", 
        headers=user1_headers, 
        json={
            "language": "en",
            "max_players": 2,
            "invitees": [user2_username],
            "base_url": "https://example.com"
        }
    )
    
    if create_game_response.status_code != 200:
        print(f"   ❌ Failed to create game: {create_game_response.status_code} {create_game_response.text}")
        return False
    
    game_data = create_game_response.json()
    game_id = game_data["id"]
    print(f"   ✅ Game created: {game_id}")
    
    # Note: Email sending might fail but the invitation is still created in the database
    if game_data.get("invitations_created", 0) == 0:
        print(f"   ❌ No invitations were created")
        return False
    
    print(f"   ✅ {game_data['invitations_created']} invitation(s) created")
    
    # Step 4: Check User2's invitations (should show 1 pending)
    print("\n4. Checking User2's pending invitations...")
    
    invitations_response = requests.get(f"{BASE_URL}/games/my-invitations", headers=user2_headers)
    
    if invitations_response.status_code != 200:
        print(f"   ❌ Failed to get invitations: {invitations_response.status_code}")
        return False
    
    invitations_data = invitations_response.json()
    pending_count_before = invitations_data["pending_count"]
    
    if pending_count_before != 1:
        print(f"   ❌ Expected 1 pending invitation, got {pending_count_before}")
        return False
    
    print(f"   ✅ User2 has {pending_count_before} pending invitation")
    
    # Step 5: User2 joins the game using regular join (not token)
    print("\n5. User2 joining game via regular join...")
    
    join_response = requests.post(f"{BASE_URL}/games/{game_id}/join", headers=user2_headers)
    
    if join_response.status_code not in [200, 201]:
        print(f"   ❌ Failed to join game: {join_response.status_code} {join_response.text}")
        return False
    
    print("   ✅ User2 joined the game successfully")
    
    # Step 6: Check User2's invitations again (should show 0 pending)
    print("\n6. Checking User2's invitations after joining...")
    
    time.sleep(1)  # Give it a moment to process
    
    invitations_response_after = requests.get(f"{BASE_URL}/games/my-invitations", headers=user2_headers)
    
    if invitations_response_after.status_code != 200:
        print(f"   ❌ Failed to get invitations: {invitations_response_after.status_code}")
        return False
    
    invitations_data_after = invitations_response_after.json()
    pending_count_after = invitations_data_after["pending_count"]
    
    if pending_count_after != 0:
        print(f"   ❌ Expected 0 pending invitations after joining, got {pending_count_after}")
        print(f"   Debug: {json.dumps(invitations_data_after, indent=2)}")
        return False
    
    print(f"   ✅ User2 now has {pending_count_after} pending invitations (invitation status updated!)")
    
    # Step 7: Verify User2 appears in the game
    print("\n7. Verifying User2 is in the game...")
    
    my_games_response = requests.get(f"{BASE_URL}/games/my-games", headers=user2_headers)
    
    if my_games_response.status_code != 200:
        print(f"   ❌ Failed to get my games: {my_games_response.status_code}")
        return False
    
    my_games_data = my_games_response.json()
    user2_games = [game for game in my_games_data["games"] if game["id"] == game_id]
    
    if len(user2_games) != 1:
        print(f"   ❌ Expected User2 to be in exactly 1 game, found {len(user2_games)}")
        return False
    
    print("   ✅ User2 appears in the game correctly")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Invitation status bug is FIXED!")
    print("✅ When a player joins a game (even without token), the invitation status is updated to 'accepted'")
    print("✅ Accepted invitations are filtered out of the my-invitations response")
    
    return True

if __name__ == "__main__":
    success = test_invitation_status_fix()
    if not success:
        print("\n❌ Test failed!")
        exit(1)
    else:
        print("\n✅ Test completed successfully!")
        exit(0) 