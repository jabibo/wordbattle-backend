#!/usr/bin/env python3
"""
Debug script to test invitation system step by step
"""
import requests
import uuid
import time

BACKEND_URL = "https://mnirejmq3g.eu-central-1.awsapprunner.com"

def register_and_auth(suffix):
    """Register user and get auth headers"""
    username = f"debug_{suffix}"
    email = f"debug_{suffix}@example.com"
    password = "debugpass123"
    
    # Register
    register_data = {"username": username, "email": email, "password": password}
    response = requests.post(f"{BACKEND_URL}/users/register", json=register_data, timeout=10)
    print(f"Register {username}: {response.status_code} - {response.text}")
    
    if response.status_code != 200:
        return None, None
    
    # Auth
    auth_data = {"username": username, "password": password}
    response = requests.post(f"{BACKEND_URL}/auth/token", data=auth_data, timeout=10)
    print(f"Auth {username}: {response.status_code} - {response.text}")
    
    if response.status_code != 200:
        return None, None
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return username, headers

def main():
    print("🔍 Debug Invitation System")
    print("=" * 40)
    
    unique_id = uuid.uuid4().hex[:6]
    
    # Step 1: Register users
    print("\n1. Register users")
    user1, headers1 = register_and_auth(f"{unique_id}_1")
    user2, headers2 = register_and_auth(f"{unique_id}_2")
    
    if not user1 or not user2:
        print("❌ Failed to register users")
        return
    
    # Step 2: Create game with invitation
    print(f"\n2. {user1} creates game and invites {user2}")
    setup_data = {
        "max_players": 2,
        "language": "de", 
        "invitees": [user2]
    }
    
    response = requests.post(f"{BACKEND_URL}/games/setup", json=setup_data, headers=headers1, timeout=10)
    print(f"Game setup: {response.status_code} - {response.text}")
    
    if response.status_code != 200:
        print("❌ Failed to create game")
        return
    
    game_data = response.json()
    game_id = game_data["game_id"]
    
    # Step 3: Check invitations immediately
    print(f"\n3. {user2} checks invitations immediately")
    response = requests.get(f"{BACKEND_URL}/games/invitations", headers=headers2, timeout=10)
    print(f"Invitations check: {response.status_code} - {response.text}")
    
    # Step 4: Wait and check again
    print(f"\n4. Wait 2 seconds and check again")
    time.sleep(2)
    response = requests.get(f"{BACKEND_URL}/games/invitations", headers=headers2, timeout=10)
    print(f"Invitations check (after wait): {response.status_code} - {response.text}")
    
    # Step 5: Check game details
    print(f"\n5. Check game details")
    response = requests.get(f"{BACKEND_URL}/games/{game_id}", headers=headers1, timeout=10)
    print(f"Game details: {response.status_code} - {response.text}")
    
    # Step 6: Test auth/me for both users
    print(f"\n6. Test auth/me for both users")
    response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers1, timeout=10)
    print(f"User1 auth/me: {response.status_code} - {response.text}")
    
    response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers2, timeout=10)
    print(f"User2 auth/me: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main() 