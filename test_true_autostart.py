#!/usr/bin/env python3
"""
Test script specifically for TRUE AUTOSTART functionality.
Tests that games automatically start when players join (not manual endpoints).
"""

import requests
import json
import random
import time

# Backend URL
BASE_URL = "https://wordbattle-backend-skhco4fxoq-ew.a.run.app"

def register_user(username: str, password: str) -> dict:
    """Register a new user and return the response."""
    response = requests.post(f"{BASE_URL}/users/register", json={
        "username": username,
        "password": password,
        "email": f"{username}@test.com"
    })
    return response.json() if response.status_code == 200 else None

def login_user(username: str, password: str) -> str:
    """Login user and return auth token."""
    response = requests.post(f"{BASE_URL}/auth/token", data={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def create_game(token: str) -> str:
    """Create a game for testing."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/games/", json={
        "language": "en",
        "max_players": 2,
        "short_game": True
    }, headers=headers)
    
    if response.status_code == 200:
        return response.json()["id"]
    print(f"❌ Failed to create game: {response.text}")
    return None

def join_game(token: str, game_id: str) -> dict:
    """Join a game and return full response."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/games/{game_id}/join", headers=headers)
    return {
        "status_code": response.status_code,
        "data": response.json() if response.status_code == 200 else response.text
    }

def get_game_info(token: str, game_id: str) -> dict:
    """Get detailed game information."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/games/{game_id}", headers=headers)
    return response.json() if response.status_code == 200 else None

def test_true_autostart():
    """Test that games automatically start when the second player joins."""
    print("🔥 TESTING TRUE AUTOSTART FUNCTIONALITY")
    print("="*60)
    print("This tests whether games automatically start when players join")
    print("(not using manual /start or /auto-start endpoints)")
    print()
    
    # Create test users
    user1_name = f"autostart1_{random.randint(1000, 9999)}"
    user2_name = f"autostart2_{random.randint(1000, 9999)}"
    password = "testpass123"
    
    print("👤 Creating test users...")
    result1 = register_user(user1_name, password)
    result2 = register_user(user2_name, password)
    
    if not result1 or not result2:
        print("❌ Failed to register users")
        return False
        
    print(f"✅ Users created: {result1['id']}, {result2['id']}")
    
    # Login users
    token1 = login_user(user1_name, password)
    token2 = login_user(user2_name, password)
    
    if not token1 or not token2:
        print("❌ Failed to login users")
        return False
        
    print("✅ Users logged in successfully")
    
    # Create game
    game_id = create_game(token1)
    if not game_id:
        return False
        
    print(f"✅ Game created: {game_id}")
    
    # Check initial game status
    print("\n🔍 Game status AFTER creation (1 player):")
    game_info = get_game_info(token1, game_id)
    if game_info:
        print(f"   Status: {game_info['status']}")
        print(f"   Current Player ID: {game_info['current_player_id']}")
        print(f"   Turn Number: {game_info['turn_number']}")
        print(f"   Phase: {game_info.get('phase', 'N/A')}")
        
        if game_info['status'] != 'setup':
            print("❌ Expected status to be 'setup' with 1 player")
            return False
    else:
        print("❌ Failed to get game info")
        return False
    
    # Join second player - this should trigger autostart
    print(f"\n🚀 CRITICAL TEST: Second player joining (should trigger autostart)...")
    join_response = join_game(token2, game_id)
    print(f"Join response: {join_response}")
    
    # Small delay to ensure database commits
    time.sleep(1)
    
    # Check game status immediately after join
    print(f"\n🔍 Game status AFTER second player joins:")
    game_info = get_game_info(token1, game_id)
    if game_info:
        print(f"   Status: {game_info['status']}")
        print(f"   Current Player ID: {game_info['current_player_id']}")
        print(f"   Turn Number: {game_info['turn_number']}")
        print(f"   Phase: {game_info.get('phase', 'N/A')}")
        print(f"   Player count: {len(game_info.get('players', {}))}")
        
        # Check if autostart worked
        if game_info['status'] == 'in_progress':
            print("✅ TRUE AUTOSTART WORKING! Game automatically started when second player joined")
            
            # Verify all autostart conditions
            success = True
            if not game_info['current_player_id']:
                print("❌ Current player ID not set")
                success = False
            if game_info['turn_number'] != 1:
                print(f"❌ Turn number should be 1, got {game_info['turn_number']}")
                success = False
            if game_info.get('phase') != 'in_progress':
                print(f"❌ Phase should be 'in_progress', got {game_info.get('phase')}")
                success = False
            
            if success:
                print("✅ All autostart conditions verified correctly!")
            else:
                print("❌ Autostart triggered but some conditions are incorrect")
            
            return success
            
        elif game_info['status'] == 'ready':
            print("❌ Game only changed to 'ready' status - autostart NOT triggered")
            print("   The game requires manual /start or /auto-start call")
            return False
        else:
            print(f"❌ Unexpected game status: {game_info['status']}")
            return False
    else:
        print("❌ Failed to get game info after join")
        return False

def main():
    print("🔥 TRUE AUTOSTART TESTING")
    print("Testing automatic game start when players join")
    print("Backend URL:", BASE_URL)
    print()
    
    success = test_true_autostart()
    
    print("\n" + "="*60)
    print("📋 FINAL RESULT")
    print("="*60)
    
    if success:
        print("✅ TRUE AUTOSTART IS WORKING!")
        print("   Games automatically start when enough players join")
    else:
        print("❌ TRUE AUTOSTART IS NOT WORKING")
        print("   Games do not automatically start when players join")
        print("   Manual /start or /auto-start calls are still required")

if __name__ == "__main__":
    main() 