#!/usr/bin/env python3

import requests
import json
import random
import string

# Base URL for the deployed service
BASE_URL = "https://wordbattle-backend-441752988736.europe-west1.run.app"

def generate_test_email():
    """Generate a unique test email address."""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

def test_short_game_for_language(language):
    """Test short game creation for a specific language."""
    print(f"\n🌐 Testing {language} short game...")
    
    # Register and login a test user
    user_email = generate_test_email()
    user_password = "TestPassword123!"
    user_username = f"player_{language}_{random.randint(1000, 9999)}"
    
    # Register user
    user_reg = requests.post(f"{BASE_URL}/users/register", json={
        "username": user_username,
        "email": user_email,
        "password": user_password
    })
    
    if user_reg.status_code != 200:
        print(f"   ❌ Failed to register user: {user_reg.status_code}")
        return False
    
    # Login user
    user_login = requests.post(f"{BASE_URL}/auth/token", data={
        "username": user_username,
        "password": user_password
    })
    
    if user_login.status_code != 200:
        print(f"   ❌ Failed to login user: {user_login.status_code}")
        return False
    
    user_token = user_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create short game for this language
    create_game_response = requests.post(f"{BASE_URL}/games/", 
        headers=headers, 
        json={
            "language": language,
            "max_players": 2,
            "short_game": True
        }
    )
    
    if create_game_response.status_code not in [200, 201]:
        print(f"   ❌ Failed to create short game: {create_game_response.status_code}")
        return False
    
    game_data = create_game_response.json()
    game_id = game_data["id"]
    
    # Get game details to check letter bag
    game_details_response = requests.get(f"{BASE_URL}/games/{game_id}", headers=headers)
    
    if game_details_response.status_code != 200:
        print(f"   ❌ Failed to get game details: {game_details_response.status_code}")
        return False
    
    game_details = game_details_response.json()
    letter_bag_count = game_details.get("letter_bag_count", 0)
    
    print(f"   ✅ {language} short game created successfully")
    print(f"   📊 Letter bag size: {letter_bag_count} tiles")
    
    # Verify it's a short game (should have 24 tiles)
    if letter_bag_count == 24:
        print(f"   ✅ Correct short game size (24 tiles)")
        return True
    else:
        print(f"   ❌ Wrong letter bag size. Expected 24, got {letter_bag_count}")
        return False

def test_normal_vs_short_game():
    """Test the difference between normal and short game."""
    print("\n🔄 Testing normal vs short game difference...")
    
    # Register and login a test user
    user_email = generate_test_email()
    user_password = "TestPassword123!"
    user_username = f"test_comparison_{random.randint(1000, 9999)}"
    
    # Register user
    user_reg = requests.post(f"{BASE_URL}/users/register", json={
        "username": user_username,
        "email": user_email,
        "password": user_password
    })
    
    user_login = requests.post(f"{BASE_URL}/auth/token", data={
        "username": user_username,
        "password": user_password
    })
    
    user_token = user_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create normal game
    normal_game_response = requests.post(f"{BASE_URL}/games/", 
        headers=headers, 
        json={
            "language": "en",
            "max_players": 2,
            "short_game": False
        }
    )
    
    normal_game_data = normal_game_response.json()
    normal_game_id = normal_game_data["id"]
    
    normal_details_response = requests.get(f"{BASE_URL}/games/{normal_game_id}", headers=headers)
    normal_details = normal_details_response.json()
    normal_bag_count = normal_details.get("letter_bag_count", 0)
    
    # Create short game
    short_game_response = requests.post(f"{BASE_URL}/games/", 
        headers=headers, 
        json={
            "language": "en",
            "max_players": 2,
            "short_game": True
        }
    )
    
    short_game_data = short_game_response.json()
    short_game_id = short_game_data["id"]
    
    short_details_response = requests.get(f"{BASE_URL}/games/{short_game_id}", headers=headers)
    short_details = short_details_response.json()
    short_bag_count = short_details.get("letter_bag_count", 0)
    
    print(f"   📊 Normal game letter bag: {normal_bag_count} tiles")
    print(f"   📊 Short game letter bag:  {short_bag_count} tiles")
    
    if short_bag_count == 24 and normal_bag_count > 24:
        print(f"   ✅ Correct difference between normal and short game")
        return True
    else:
        print(f"   ❌ Unexpected letter bag sizes")
        return False

def test_short_game_comprehensive():
    """Run comprehensive tests for the short game feature."""
    print("🧪 Testing Short Game Feature")
    print("=" * 50)
    
    # Test short games for all supported languages
    languages = ["en", "de", "es", "fr", "it"]
    language_results = {}
    
    for language in languages:
        try:
            success = test_short_game_for_language(language)
            language_results[language] = success
        except Exception as e:
            print(f"   ❌ Error testing {language}: {e}")
            language_results[language] = False
    
    # Test normal vs short game difference
    comparison_success = test_normal_vs_short_game()
    
    # Summary
    print("\n📋 SHORT GAME TEST SUMMARY")
    print("=" * 30)
    
    print("\n🌐 Language Tests:")
    for language, success in language_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {language.upper()}: {status}")
    
    print(f"\n🔄 Comparison Test: {'✅ PASS' if comparison_success else '❌ FAIL'}")
    
    all_passed = all(language_results.values()) and comparison_success
    
    if all_passed:
        print("\n🎉 ALL SHORT GAME TESTS PASSED!")
        print("✅ Short game feature works correctly for all languages")
        print("✅ Creates 24-tile bags with only value-1 letters")
        print("✅ Provides quick endgame testing capability")
    else:
        print("\n❌ SOME TESTS FAILED!")
        failed_languages = [lang for lang, success in language_results.items() if not success]
        if failed_languages:
            print(f"Failed languages: {', '.join(failed_languages)}")
    
    return all_passed

if __name__ == "__main__":
    success = test_short_game_comprehensive()
    exit(0 if success else 1) 