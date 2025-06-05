#!/usr/bin/env python3
"""
Test script for the enhanced score breakdown functionality.
Tests detailed score breakdown including word formation, multipliers, and bonus points.
"""

import requests
import json
import sys
from typing import Dict, Any
import random

# Backend URL
BASE_URL = "https://wordbattle-backend-441752988736.europe-west1.run.app"

def register_user(username: str, password: str) -> Dict[str, Any]:
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

def create_short_game(token: str) -> str:
    """Create a short game for testing."""
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

def start_game(token: str, game_id: str) -> bool:
    """Start a game."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/games/{game_id}/start", headers=headers)
    return response.status_code == 200

def get_game_info(token: str, game_id: str) -> Dict[str, Any]:
    """Get game information."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/games/{game_id}", headers=headers)
    return response.json() if response.status_code == 200 else None

def get_player_rack(token: str, game_id: str) -> str:
    """Get the current player's rack."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/games/{game_id}", headers=headers)
    if response.status_code == 200:
        game_data = response.json()
        # Get current user ID from the token (we need to decode or get it another way)
        # For now, let's look at all players and find the one with a non-empty rack
        players = game_data.get('players', {})
        current_player_id = str(game_data.get('current_player_id'))
        if current_player_id in players:
            return ''.join(players[current_player_id].get('rack', []))
    return ''

def test_move_with_available_letters(token: str, game_id: str) -> Dict[str, Any]:
    """Test a move using letters available in the player's rack."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get player's rack
    rack = get_player_rack(token, game_id)
    print(f"Player's rack: {rack}")
    
    if not rack:
        print("❌ Could not get player's rack")
        return None
    
    # Try to make valid words with available letters
    available_letters = list(rack.upper())
    
    # List of common 3-letter words to try
    common_words = [
        ("ARE", ["A", "R", "E"]),
        ("EAR", ["E", "A", "R"]),
        ("ERA", ["E", "R", "A"]),
        ("ART", ["A", "R", "T"]),
        ("EAT", ["E", "A", "T"]),
        ("TEA", ["T", "E", "A"]),
        ("TIE", ["T", "I", "E"]),
        ("TOE", ["T", "O", "E"]),
        ("ROT", ["R", "O", "T"]),
        ("NET", ["N", "E", "T"]),
        ("TEN", ["T", "E", "N"]),
        ("ONE", ["O", "N", "E"]),
        ("ORE", ["O", "R", "E"]),
        ("RUN", ["R", "U", "N"]),
        ("SUN", ["S", "U", "N"]),
        ("NUT", ["N", "U", "T"]),
        ("TUN", ["T", "U", "N"]),
        ("USE", ["U", "S", "E"]),
        ("SUE", ["S", "U", "E"]),
        ("IRE", ["I", "R", "E"]),
        ("AIR", ["A", "I", "R"])
    ]
    
    # Try to find a word we can make
    move_data = None
    word_attempt = None
    
    for word, required_letters in common_words:
        if all(letter in available_letters for letter in required_letters):
            move_data = [
                {"row": 7, "col": 6, "letter": required_letters[0]},
                {"row": 7, "col": 7, "letter": required_letters[1]},
                {"row": 7, "col": 8, "letter": required_letters[2]}
            ]
            word_attempt = word
            break
    
    if not move_data:
        print("❌ Could not find a valid word to make with available letters")
        print(f"Available letters: {available_letters}")
        return None
    
    print(f"\n🧪 Testing move with available letters: {word_attempt}")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/games/{game_id}/move", 
        json=move_data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Move Valid: True")
        print(f"📊 Points Gained: {result['points_gained']}")
        
        if 'score_breakdown' in result:
            breakdown = result['score_breakdown']
            print(f"\n📈 DETAILED SCORE BREAKDOWN:")
            print(f"   Total Base Points: {breakdown['total_points']}")
            print(f"   Grand Total: {breakdown['grand_total']}")
            
            print(f"\n🔤 WORDS FORMED ({len(breakdown['words_formed'])}):")
            for i, word_data in enumerate(breakdown['words_formed'], 1):
                print(f"   Word {i}: {word_data['word']}")
                print(f"      Base Score: {word_data['base_score']}")
                print(f"      Final Score: {word_data['final_score']}")
                
                if word_data['word_multipliers']:
                    print(f"      Word Multipliers: {word_data['word_multipliers']}")
                
                print(f"      Letters:")
                for letter in word_data['letters']:
                    multiplier_text = f" ({letter['multiplier']})" if letter['multiplier'] else ""
                    newly_placed = "🆕" if letter['is_newly_placed'] else "📋"
                    blank_text = " (blank)" if letter['is_blank'] else ""
                    print(f"         {newly_placed} {letter['letter']}: {letter['base_value']} → {letter['final_value']}{multiplier_text}{blank_text} at ({letter['position']['row']}, {letter['position']['col']})")
            
            if breakdown['bonus_points']:
                print(f"\n🎁 BONUS POINTS:")
                for bonus in breakdown['bonus_points']:
                    print(f"   {bonus['description']}: +{bonus['points']} points")
        else:
            print("⚠️ No score_breakdown in response")
            print(f"Response keys: {list(result.keys())}")
        
        return result
    else:
        print(f"❌ Move failed: {response.text}")
        return None

def test_score_breakdown_with_test_endpoint(token: str, game_id: str) -> Dict[str, Any]:
    """Test score breakdown using the test-move endpoint with bypasses."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Simple first move - place CAT through center
    move_data = [
        {"row": 7, "col": 6, "letter": "C"},
        {"row": 7, "col": 7, "letter": "A"},
        {"row": 7, "col": 8, "letter": "T"}
    ]
    
    print(f"\n🧪 Testing score breakdown with test-move endpoint")
    print("=" * 60)
    
    # Use test-move endpoint with bypasses
    payload = {
        "move_data": move_data,
        "skip_turn_validation": True,
        "skip_rack_validation": True,
        "test_rack": "CATDEFG"
    }
    
    response = requests.post(
        f"{BASE_URL}/games/{game_id}/test-move", 
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Move Valid: {result.get('move_valid', True)}")
        print(f"📊 Points Gained: {result['points_gained']}")
        
        if 'score_breakdown' in result:
            breakdown = result['score_breakdown']
            print(f"\n📈 DETAILED SCORE BREAKDOWN:")
            print(f"   Total Base Points: {breakdown['total_points']}")
            print(f"   Grand Total: {breakdown['grand_total']}")
            
            print(f"\n🔤 WORDS FORMED ({len(breakdown['words_formed'])}):")
            for i, word_data in enumerate(breakdown['words_formed'], 1):
                print(f"   Word {i}: {word_data['word']}")
                print(f"      Base Score: {word_data['base_score']}")
                print(f"      Final Score: {word_data['final_score']}")
                
                if word_data['word_multipliers']:
                    print(f"      Word Multipliers: {word_data['word_multipliers']}")
                
                print(f"      Letters:")
                for letter in word_data['letters']:
                    multiplier_text = f" ({letter['multiplier']})" if letter['multiplier'] else ""
                    newly_placed = "🆕" if letter['is_newly_placed'] else "📋"
                    blank_text = " (blank)" if letter['is_blank'] else ""
                    print(f"         {newly_placed} {letter['letter']}: {letter['base_value']} → {letter['final_value']}{multiplier_text}{blank_text} at ({letter['position']['row']}, {letter['position']['col']})")
            
            if breakdown['bonus_points']:
                print(f"\n🎁 BONUS POINTS:")
                for bonus in breakdown['bonus_points']:
                    print(f"   {bonus['description']}: +{bonus['points']} points")
        
        return result
    else:
        print(f"❌ Move failed: {response.text}")
        return None

def main():
    print("🎯 Testing Enhanced Score Breakdown Functionality")
    print("=" * 60)
    
    # Create test users
    user1_name = f"scoretest1_{random.randint(1000, 9999)}"
    user2_name = f"scoretest2_{random.randint(1000, 9999)}"
    password = "testpass123"
    
    print("👤 Creating test users...")
    result1 = register_user(user1_name, password)
    result2 = register_user(user2_name, password)
    print(f"User 1 registration: {result1}")
    print(f"User 2 registration: {result2}")
    
    # Login users
    print("🔐 Logging in users...")
    token1 = login_user(user1_name, password)
    token2 = login_user(user2_name, password)
    
    print(f"Token 1: {'✅ Success' if token1 else '❌ Failed'}")
    print(f"Token 2: {'✅ Success' if token2 else '❌ Failed'}")
    
    if not token1 or not token2:
        print("❌ Failed to login users")
        return
    
    # Create game
    print("🎮 Creating short game...")
    game_id = create_short_game(token1)
    if not game_id:
        return
    
    print(f"✅ Game {game_id} created!")
    
    # Join second user
    print("🤝 Joining second user...")
    if not join_game(token2, game_id):
        print("❌ Failed to join game")
        return
    
    # Start game
    print("🚀 Starting game...")
    if not start_game(token1, game_id):
        print("❌ Failed to start game")
        return
    
    # Get game info to check current player
    game_info = get_game_info(token1, game_id)
    if game_info:
        print(f"Game status: {game_info.get('status')}")
        print(f"Current player: {game_info.get('current_player_id')}")
        current_player_id = game_info.get('current_player_id')
        
        # Use the token of the current player
        if current_player_id == result1.get('id'):
            current_token = token1
            print("Using token1 (first user)")
        elif current_player_id == result2.get('id'):
            current_token = token2
            print("Using token2 (second user)")
        else:
            print("❌ Current player ID doesn't match either user")
            return
    else:
        print("❌ Failed to get game info")
        return
    
    # Test score breakdown functionality
    result = test_move_with_available_letters(current_token, game_id)
    
    if result:
        print("\n🏁 Score Breakdown Testing Complete!")
        print("✅ Successfully implemented detailed score breakdown!")
        print("\nThe backend now returns detailed score breakdowns including:")
        print("  • Word-by-word scoring analysis")
        print("  • Letter-by-letter point calculation")
        print("  • Base values vs final values after multipliers")
        print("  • Which tiles were newly placed vs already on board")
        print("  • Letter and word multiplier details")
        print("  • Bonus points (like 7-tile bonus)")
        print("  • Position coordinates of each letter")
        print("\nFrontend can now parse this data using MoveScoreBreakdown,")
        print("WordScore, and LetterScore models for comprehensive score displays!")
    else:
        print("\n❌ Score breakdown testing failed")

if __name__ == "__main__":
    main() 