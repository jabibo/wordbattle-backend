#!/usr/bin/env python3
"""
Test script to check token expiration issues
"""
import requests
import uuid
import time
from datetime import datetime
import jwt

BACKEND_URL = "https://mnirejmq3g.eu-central-1.awsapprunner.com"

def decode_token(token):
    """Decode JWT token to check expiration"""
    try:
        # Decode without verification to see the payload
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = decoded.get('exp', 0)
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        current_time = datetime.now()
        
        print(f"Token expires at: {exp_datetime}")
        print(f"Current time: {current_time}")
        print(f"Time until expiry: {exp_datetime - current_time}")
        print(f"Token valid: {current_time < exp_datetime}")
        
        return current_time < exp_datetime
    except Exception as e:
        print(f"Error decoding token: {e}")
        return False

def test_token_expiry():
    """Test if token expiration is causing the invitation issue"""
    print("🕐 Testing Token Expiration Issue")
    print("=" * 40)
    
    unique_id = uuid.uuid4().hex[:6]
    
    # Step 1: Register user1
    print("\n1. Register user1")
    username1 = f"token_test_{unique_id}_1"
    email1 = f"token_test_{unique_id}_1@example.com"
    password = "testpass123"
    
    register_data = {"username": username1, "email": email1, "password": password}
    response = requests.post(f"{BACKEND_URL}/users/register", json=register_data, timeout=10)
    print(f"Register user1: {response.status_code}")
    
    if response.status_code != 200:
        print("❌ Failed to register user1")
        return
    
    # Get token for user1
    auth_data = {"username": username1, "password": password}
    response = requests.post(f"{BACKEND_URL}/auth/token", data=auth_data, timeout=10)
    print(f"Auth user1: {response.status_code}")
    
    if response.status_code != 200:
        print("❌ Failed to authenticate user1")
        return
    
    token1 = response.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    print(f"\n🔍 User1 token analysis:")
    decode_token(token1)
    
    # Step 2: Register user2
    print(f"\n2. Register user2")
    username2 = f"token_test_{unique_id}_2"
    email2 = f"token_test_{unique_id}_2@example.com"
    
    register_data = {"username": username2, "email": email2, "password": password}
    response = requests.post(f"{BACKEND_URL}/users/register", json=register_data, timeout=10)
    print(f"Register user2: {response.status_code}")
    
    if response.status_code != 200:
        print("❌ Failed to register user2")
        return
    
    # Get token for user2
    auth_data = {"username": username2, "password": password}
    response = requests.post(f"{BACKEND_URL}/auth/token", data=auth_data, timeout=10)
    print(f"Auth user2: {response.status_code}")
    
    if response.status_code != 200:
        print("❌ Failed to authenticate user2")
        return
    
    token2 = response.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    print(f"\n🔍 User2 token analysis:")
    decode_token(token2)
    
    # Step 3: Create game immediately
    print(f"\n3. User1 creates game immediately")
    setup_data = {
        "max_players": 2,
        "language": "de",
        "invitees": [username2]
    }
    
    response = requests.post(f"{BACKEND_URL}/games/setup", json=setup_data, headers=headers1, timeout=10)
    print(f"Game setup: {response.status_code} - {response.text}")
    
    if response.status_code != 200:
        print("❌ Failed to create game")
        return
    
    game_id = response.json()["game_id"]
    
    # Step 4: Check invitations immediately
    print(f"\n4. User2 checks invitations immediately")
    print(f"🔍 User2 token status before invitation check:")
    is_valid = decode_token(token2)
    
    response = requests.get(f"{BACKEND_URL}/games/invitations", headers=headers2, timeout=10)
    print(f"Invitations check: {response.status_code} - {response.text}")
    
    # Step 5: Test auth/me to see if token is still valid
    print(f"\n5. Test auth/me for user2")
    response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers2, timeout=10)
    print(f"Auth/me: {response.status_code} - {response.text}")
    
    # Step 6: Try with fresh token
    print(f"\n6. Get fresh token for user2 and try again")
    auth_data = {"username": username2, "password": password}
    response = requests.post(f"{BACKEND_URL}/auth/token", data=auth_data, timeout=10)
    
    if response.status_code == 200:
        fresh_token = response.json()["access_token"]
        fresh_headers = {"Authorization": f"Bearer {fresh_token}"}
        
        print(f"🔍 Fresh token analysis:")
        decode_token(fresh_token)
        
        response = requests.get(f"{BACKEND_URL}/games/invitations", headers=fresh_headers, timeout=10)
        print(f"Invitations with fresh token: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_token_expiry() 