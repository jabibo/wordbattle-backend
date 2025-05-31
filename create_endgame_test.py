#!/usr/bin/env python3

"""
Endgame Testing Script for WordBattle

This script enables endgame testing mode by:
1. Setting the TEST_MODE_ENDGAME environment variable
2. Creating a test game with reduced letter bag (24 tiles)
3. Providing instructions for testing endgame scenarios

Usage:
    python create_endgame_test.py
"""

import os
import sys
import requests
import json

# Service URL
SERVICE_URL = "https://wordbattle-backend-441752988736.europe-west1.run.app"

def enable_test_mode():
    """Enable test mode by setting environment variable."""
    os.environ["TEST_MODE_ENDGAME"] = "true"
    print("🧪 TEST MODE ENABLED: Letter bag reduced to 24 tiles")

def create_test_game():
    """Create a test game with endgame mode."""
    print("\n📋 CREATING ENDGAME TEST GAME")
    print("="*50)
    
    # Get tokens for testing
    response = requests.get(f"{SERVICE_URL}/debug/tokens")
    if response.status_code != 200:
        print("❌ Failed to get debug tokens")
        return None
    
    tokens = response.json()
    player1_token = tokens["tokens"]["player01"]["token"]
    player2_token = tokens["tokens"]["player02"]["token"]
    
    print(f"✅ Got tokens for player01 and player02")
    
    # Create a new game
    game_data = {
        "language": "en",
        "max_players": 2
    }
    
    response = requests.post(
        f"{SERVICE_URL}/games/",
        headers={"Authorization": f"Bearer {player1_token}"},
        json=game_data
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create game: {response.status_code}")
        print(response.text)
        return None
    
    game = response.json()
    game_id = game["id"]
    print(f"✅ Created game: {game_id}")
    
    # Join with player02
    response = requests.post(
        f"{SERVICE_URL}/games/{game_id}/join",
        headers={"Authorization": f"Bearer {player2_token}"}
    )
    
    if response.status_code in [200, 409]:  # 409 means already joined
        print(f"✅ Player02 joined game")
    else:
        print(f"⚠️  Player02 join status: {response.status_code}")
    
    # Start the game
    response = requests.post(
        f"{SERVICE_URL}/games/{game_id}/start",
        headers={"Authorization": f"Bearer {player1_token}"}
    )
    
    if response.status_code == 200:
        print(f"✅ Game started successfully")
    else:
        print(f"❌ Failed to start game: {response.status_code}")
        print(response.text)
        return None
    
    return {
        "game_id": game_id,
        "player1_token": player1_token,
        "player2_token": player2_token
    }

def show_game_info(game_info):
    """Show information about the test game."""
    if not game_info:
        return
    
    print("\n🎯 ENDGAME TEST GAME READY")
    print("="*50)
    print(f"Game ID: {game_info['game_id']}")
    print("\n📝 TESTING INSTRUCTIONS:")
    print("1. The letter bag now contains only 24 tiles instead of 100")
    print("2. English tiles: E(5), A(4), I(4), O(3), N(3), R(2), T(2), S(1)")
    print("3. After each player gets 7 tiles (14 total), only 10 tiles remain")
    print("4. This will trigger endgame scenarios much faster")
    
    print("\n🔧 TEST COMMANDS:")
    print(f"# Check game state:")
    print(f"curl -H 'Authorization: Bearer {game_info['player1_token']}' '{SERVICE_URL}/games/{game_info['game_id']}'")
    
    print(f"\n# Get current rack:")
    print(f"curl -H 'Authorization: Bearer {game_info['player1_token']}' '{SERVICE_URL}/games/{game_info['game_id']}/rack'")
    
    print(f"\n# Make a test move (example - adapt positions/letters to your rack):")
    print(f"curl -X POST -H 'Content-Type: application/json' -H 'Authorization: Bearer {game_info['player1_token']}' -d '[{{\"row\":7,\"col\":7,\"letter\":\"E\"}}]' '{SERVICE_URL}/games/{game_info['game_id']}/move'")
    
    print("\n⚡ ENDGAME TRIGGERS:")
    print("- Game ends when letter bag is empty AND one player uses all tiles")
    print("- Game ends after 6 consecutive passes")
    print("- Remaining tiles in rack are subtracted from final score")
    print("- Player who empties rack gets bonus points from other players' remaining tiles")

def main():
    print("🎮 WORDBATTLE ENDGAME TESTING SETUP")
    print("="*60)
    
    # Enable test mode
    enable_test_mode()
    
    # Create test game
    game_info = create_test_game()
    
    # Show instructions
    show_game_info(game_info)
    
    print(f"\n💡 To disable test mode later, run:")
    print(f"unset TEST_MODE_ENDGAME")
    
    return game_info is not None

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 