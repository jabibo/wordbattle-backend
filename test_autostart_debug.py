#!/usr/bin/env python3
"""
Comprehensive test script for game start logic debugging.
Tests both manual start and auto-start scenarios.
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

def get_games_list(token: str) -> dict:
    """Get games list from my-games API."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/games/my-games", headers=headers)
    return response.json() if response.status_code == 200 else None

def start_game_manual(token: str, game_id: str) -> dict:
    """Start a game manually and return response."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/games/{game_id}/start", headers=headers)
    return {
        "status_code": response.status_code,
        "data": response.json() if response.status_code == 200 else response.text
    }

def start_game_auto(token: str, game_id: str) -> dict:
    """Auto-start a game and return response."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/games/{game_id}/auto-start", headers=headers)
    return {
        "status_code": response.status_code,
        "data": response.json() if response.status_code == 200 else response.text
    }

def check_api_consistency(token: str, game_id: str) -> dict:
    """Check consistency between individual game API and games list API."""
    print("\n🔍 API Consistency Check:")
    
    # Get individual game details
    individual_game = get_game_info(token, game_id)
    games_list_response = get_games_list(token)
    
    if not individual_game:
        return {"error": "Failed to get individual game info"}
    
    if not games_list_response or "games" not in games_list_response:
        return {"error": "Failed to get games list"}
    
    # Find our game in the list
    our_game_in_list = None
    for game in games_list_response["games"]:
        if game["id"] == game_id:
            our_game_in_list = game
            break
    
    if not our_game_in_list:
        return {"error": "Game not found in games list"}
    
    # Compare key fields
    comparison = {
        "individual_api": {
            "current_player_id": individual_game.get("current_player_id"),
            "turn_number": individual_game.get("turn_number"),
            "status": individual_game.get("status")
        },
        "games_list_api": {
            "current_player_id": our_game_in_list.get("current_player_id"),
            "turn_number": our_game_in_list.get("turn_number"),
            "status": our_game_in_list.get("status"),
            "is_user_turn": our_game_in_list.get("is_user_turn")
        },
        "consistency_check": {}
    }
    
    # Check consistency
    comparison["consistency_check"]["current_player_id_matches"] = (
        comparison["individual_api"]["current_player_id"] == 
        comparison["games_list_api"]["current_player_id"]
    )
    comparison["consistency_check"]["turn_number_matches"] = (
        comparison["individual_api"]["turn_number"] == 
        comparison["games_list_api"]["turn_number"]
    )
    comparison["consistency_check"]["status_matches"] = (
        comparison["individual_api"]["status"] == 
        comparison["games_list_api"]["status"]
    )
    
    return comparison

def test_manual_start():
    """Test manual game start logic."""
    print("\n" + "="*80)
    print("🧪 TESTING MANUAL GAME START LOGIC")
    print("="*80)
    
    # Create test users
    user1_name = f"manual1_{random.randint(1000, 9999)}"
    user2_name = f"manual2_{random.randint(1000, 9999)}"
    password = "testpass123"
    
    print("👤 Creating test users...")
    result1 = register_user(user1_name, password)
    result2 = register_user(user2_name, password)
    
    if not result1 or not result2:
        print("❌ Failed to register users")
        return None
        
    print(f"✅ Users created: {result1['id']}, {result2['id']}")
    
    # Login users
    token1 = login_user(user1_name, password)
    token2 = login_user(user2_name, password)
    
    if not token1 or not token2:
        print("❌ Failed to login users")
        return None
        
    print("✅ Users logged in successfully")
    
    # Create game
    game_id = create_game(token1)
    if not game_id:
        return None
        
    print(f"✅ Game created: {game_id}")
    
    # Join second player
    if not join_game(token2, game_id):
        print("❌ Failed to join second player")
        return None
        
    print("✅ Second player joined")
    
    # Check game status before start
    print("\n🔍 Game status BEFORE manual start:")
    game_info = get_game_info(token1, game_id)
    if game_info:
        print(f"   Status: {game_info['status']}")
        print(f"   Current Player ID: {game_info['current_player_id']}")
        print(f"   Turn Number: {game_info['turn_number']}")
    
    # Start the game manually
    print("\n🚀 Starting game manually...")
    start_response = start_game_manual(token1, game_id)
    print(f"Manual start response: {start_response}")
    
    # Check game status after start
    print("\n🔍 Game status AFTER manual start:")
    game_info = get_game_info(token1, game_id)
    if game_info:
        print(f"   Status: {game_info['status']}")
        print(f"   Current Player ID: {game_info['current_player_id']}")
        print(f"   Turn Number: {game_info['turn_number']}")
        
        if game_info['current_player_id'] and game_info['turn_number'] == 1:
            print("✅ Manual start WORKING CORRECTLY")
        else:
            print("❌ Manual start STILL HAS ISSUES")
    
    # Check API consistency
    consistency = check_api_consistency(token1, game_id)
    print(f"\n📊 API Consistency Results:")
    print(json.dumps(consistency, indent=2))
    
    return game_id

def test_auto_start():
    """Test auto-start game logic."""
    print("\n" + "="*80)
    print("🤖 TESTING AUTO-START GAME LOGIC")
    print("="*80)
    
    # Create test users
    user1_name = f"auto1_{random.randint(1000, 9999)}"
    user2_name = f"auto2_{random.randint(1000, 9999)}"
    password = "testpass123"
    
    print("👤 Creating test users...")
    result1 = register_user(user1_name, password)
    result2 = register_user(user2_name, password)
    
    if not result1 or not result2:
        print("❌ Failed to register users")
        return None
        
    print(f"✅ Users created: {result1['id']}, {result2['id']}")
    
    # Login users
    token1 = login_user(user1_name, password)
    token2 = login_user(user2_name, password)
    
    if not token1 or not token2:
        print("❌ Failed to login users")
        return None
        
    print("✅ Users logged in successfully")
    
    # Create game
    game_id = create_game(token1)
    if not game_id:
        return None
        
    print(f"✅ Game created: {game_id}")
    
    # Join second player
    if not join_game(token2, game_id):
        print("❌ Failed to join second player")
        return None
        
    print("✅ Second player joined")
    
    # Check game status before auto-start
    print("\n🔍 Game status BEFORE auto-start:")
    game_info = get_game_info(token1, game_id)
    if game_info:
        print(f"   Status: {game_info['status']}")
        print(f"   Current Player ID: {game_info['current_player_id']}")
        print(f"   Turn Number: {game_info['turn_number']}")
    
    # Auto-start the game
    print("\n🤖 Auto-starting game...")
    start_response = start_game_auto(token1, game_id)
    print(f"Auto-start response: {start_response}")
    
    # Check game status after auto-start
    print("\n🔍 Game status AFTER auto-start:")
    game_info = get_game_info(token1, game_id)
    if game_info:
        print(f"   Status: {game_info['status']}")
        print(f"   Current Player ID: {game_info['current_player_id']}")
        print(f"   Turn Number: {game_info['turn_number']}")
        
        if game_info['current_player_id'] and game_info['turn_number'] == 1:
            print("✅ Auto-start WORKING CORRECTLY")
        else:
            print("❌ Auto-start STILL HAS ISSUES")
    
    # Check API consistency
    consistency = check_api_consistency(token1, game_id)
    print(f"\n📊 API Consistency Results:")
    print(json.dumps(consistency, indent=2))
    
    return game_id

def main():
    print("🔍 COMPREHENSIVE GAME START DEBUGGING")
    print("Testing both manual and auto-start scenarios")
    print("Backend URL:", BASE_URL)
    
    # Test manual start
    manual_game_id = test_manual_start()
    
    # Test auto-start
    auto_game_id = test_auto_start()
    
    print("\n" + "="*80)
    print("📋 SUMMARY")
    print("="*80)
    print(f"Manual start game ID: {manual_game_id}")
    print(f"Auto-start game ID: {auto_game_id}")
    
    if manual_game_id and auto_game_id:
        print("✅ Both test scenarios completed successfully")
    else:
        print("❌ Some test scenarios failed")

if __name__ == "__main__":
    main() 