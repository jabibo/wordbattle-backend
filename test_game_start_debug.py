#!/usr/bin/env python3
"""
Debug script to test game start logic and current_player_id setting.
"""

import requests
import json
import random

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

def join_game(token: str, game_id: str) -> bool:
    """Join a game."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/games/{game_id}/join", headers=headers)
    return response.status_code == 200

def get_game_info(token: str, game_id: str) -> dict:
    """Get detailed game information."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/games/{game_id}", headers=headers)
    return response.json() if response.status_code == 200 else None

def start_game(token: str, game_id: str) -> dict:
    """Start a game and return response."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/games/{game_id}/start", headers=headers)
    return {
        "status_code": response.status_code,
        "data": response.json() if response.status_code == 200 else response.text
    }

def debug_game_start():
    print("🔍 Debugging Game Start Logic")
    print("=" * 60)
    
    # Create test users
    user1_name = f"starttest1_{random.randint(1000, 9999)}"
    user2_name = f"starttest2_{random.randint(1000, 9999)}"
    password = "testpass123"
    
    print("👤 Creating test users...")
    result1 = register_user(user1_name, password)
    result2 = register_user(user2_name, password)
    
    if not result1 or not result2:
        print("❌ Failed to register users")
        return
        
    print(f"✅ Users created: {result1['id']}, {result2['id']}")
    
    # Login users
    token1 = login_user(user1_name, password)
    token2 = login_user(user2_name, password)
    
    if not token1 or not token2:
        print("❌ Failed to login users")
        return
        
    print("✅ Users logged in successfully")
    
    # Create game
    game_id = create_game(token1)
    if not game_id:
        return
        
    print(f"✅ Game created: {game_id}")
    
    # Check game info before joining second player
    print("\n🔍 Game info BEFORE second player joins:")
    game_info = get_game_info(token1, game_id)
    if game_info:
        print(f"   Status: {game_info['status']}")
        print(f"   Current Player ID: {game_info['current_player_id']}")
        print(f"   Turn Number: {game_info['turn_number']}")
        print(f"   Players: {list(game_info['players'].keys())}")
    
    # Join second player
    if not join_game(token2, game_id):
        print("❌ Failed to join second player")
        return
        
    print("✅ Second player joined")
    
    # Check game info after joining
    print("\n🔍 Game info AFTER second player joins:")
    game_info = get_game_info(token1, game_id)
    if game_info:
        print(f"   Status: {game_info['status']}")
        print(f"   Current Player ID: {game_info['current_player_id']}")
        print(f"   Turn Number: {game_info['turn_number']}")
        print(f"   Players: {list(game_info['players'].keys())}")
    
    # Start the game
    print("\n🚀 Starting game...")
    start_response = start_game(token1, game_id)
    print(f"Start response: {start_response}")
    
    # Check game info after starting
    print("\n🔍 Game info AFTER starting:")
    game_info = get_game_info(token1, game_id)
    if game_info:
        print(f"   Status: {game_info['status']}")
        print(f"   Current Player ID: {game_info['current_player_id']}")
        print(f"   Turn Number: {game_info['turn_number']}")
        print(f"   Players: {list(game_info['players'].keys())}")
        print(f"   Players info: {game_info['players']}")
        
        # Check if current_player_id matches one of the players
        player_ids = [int(pid) for pid in game_info['players'].keys()]
        current_player = game_info['current_player_id']
        print(f"   Player IDs: {player_ids}")
        print(f"   Current Player: {current_player}")
        print(f"   Is Current Player Valid? {current_player in player_ids}")
    
    # Also check via games list API
    print("\n🔍 Checking via my-games API:")
    headers = {"Authorization": f"Bearer {token1}"}
    response = requests.get(f"{BASE_URL}/games/my-games", headers=headers)
    if response.status_code == 200:
        games = response.json()["games"]
        our_game = next((g for g in games if g["id"] == game_id), None)
        if our_game:
            print(f"   Status: {our_game['status']}")
            # Print all available fields to debug
            print(f"   Available fields: {list(our_game.keys())}")
            if 'debug_deployment_test' in our_game:
                print(f"   🎯 Debug Field: {our_game['debug_deployment_test']}")
            else:
                print(f"   ❌ debug_deployment_test field MISSING - deployment issue!")
            if 'current_player_id' in our_game:
                print(f"   Current Player ID: {our_game['current_player_id']}")
            else:
                print(f"   ❌ current_player_id field MISSING")
            if 'turn_number' in our_game:
                print(f"   Turn Number: {our_game['turn_number']}")
            else:
                print(f"   ❌ turn_number field MISSING")
            if 'is_user_turn' in our_game:
                print(f"   Is User Turn: {our_game['is_user_turn']}")
            else:
                print(f"   ❌ is_user_turn field MISSING")
    else:
        print(f"   ❌ API Error: {response.status_code} - {response.text}")
    
    # Check the raw game state JSON for turn number
    print("\n🔍 Checking raw game state JSON:")
    if game_info and 'state' in game_info:
        # This won't work since individual API doesn't return raw state, but let's see what we have
        print("   Raw state not exposed in API")
    else:
        print("   State field not available in individual game API")

if __name__ == "__main__":
    debug_game_start() 