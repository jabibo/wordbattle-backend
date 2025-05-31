#!/usr/bin/env python3

"""
Comprehensive test for the Word Admin System functionality.
This test verifies all features including privilege management, word addition, and downloads.
"""

import requests
import json
import sys

# The deployed service URL
SERVICE_URL = "https://wordbattle-backend-441752988736.europe-west1.run.app"

def print_step(step_number, description):
    print(f"\n{'='*60}")
    print(f"STEP {step_number}: {description}")
    print(f"{'='*60}")

def print_result(success, message):
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"{status}: {message}")

def test_word_admin_system():
    """Test the complete word admin system."""
    print("🧪 TESTING WORD ADMIN SYSTEM")
    print("="*70)
    
    # Get debug tokens
    print_step(1, "Getting test tokens")
    response = requests.get(f"{SERVICE_URL}/debug/tokens")
    if response.status_code != 200:
        print_result(False, "Failed to get debug tokens")
        return False
    
    tokens_data = response.json()
    admin_token = tokens_data["tokens"]["admin"]["token"]
    player1_token = tokens_data["tokens"]["player01"]["token"]
    player2_token = tokens_data["tokens"]["player02"]["token"]
    
    print_result(True, "Retrieved test tokens")
    
    # Test 2: Check initial word admin status (should be False for regular users)
    print_step(2, "Checking initial word admin status")
    response = requests.get(
        f"{SERVICE_URL}/word-admin/status", 
        headers={"Authorization": f"Bearer {player1_token}"}
    )
    if response.status_code == 200:
        status_data = response.json()
        is_word_admin = status_data.get("is_word_admin", False)
        print_result(not is_word_admin, f"Player initial status: word_admin={is_word_admin}")
    else:
        print_result(False, f"Failed to get word admin status: {response.status_code}")
    
    # Test 3: Try adding word without privileges (should fail)
    print_step(3, "Testing word addition without privileges")
    response = requests.post(
        f"{SERVICE_URL}/word-admin/add-word",
        headers={"Authorization": f"Bearer {player1_token}"},
        json={"word": "TESTWORD", "language": "en"}
    )
    expected_failure = response.status_code == 403
    print_result(expected_failure, f"Unprivileged word addition properly rejected: {response.status_code}")
    
    # Test 4: Grant word admin privileges (admin only)
    print_step(4, "Granting word admin privileges")
    
    # First get the user ID for player01
    response = requests.get(
        f"{SERVICE_URL}/word-admin/status", 
        headers={"Authorization": f"Bearer {player1_token}"}
    )
    if response.status_code == 200:
        player1_user_id = response.json()["user_id"]
        
        # Grant privileges as admin
        response = requests.post(
            f"{SERVICE_URL}/word-admin/grant-word-admin",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"user_id": player1_user_id, "is_word_admin": True}
        )
        success = response.status_code == 200
        print_result(success, f"Word admin privilege granted: {response.status_code}")
        if success:
            print(f"    Response: {response.json()['message']}")
    else:
        print_result(False, "Could not get player user ID")
        return False
    
    # Test 5: Verify privilege grant
    print_step(5, "Verifying word admin privilege")
    response = requests.get(
        f"{SERVICE_URL}/word-admin/status", 
        headers={"Authorization": f"Bearer {player1_token}"}
    )
    if response.status_code == 200:
        status_data = response.json()
        is_word_admin = status_data.get("is_word_admin", False)
        can_manage = status_data.get("can_manage_words", False)
        print_result(is_word_admin and can_manage, f"Word admin status: {is_word_admin}, can_manage: {can_manage}")
    else:
        print_result(False, f"Failed to verify privilege: {response.status_code}")
    
    # Test 6: Add a single word
    print_step(6, "Adding a single word")
    response = requests.post(
        f"{SERVICE_URL}/word-admin/add-word",
        headers={"Authorization": f"Bearer {player1_token}"},
        json={"word": "TESTWORD", "language": "en"}
    )
    success = response.status_code == 200
    print_result(success, f"Single word addition: {response.status_code}")
    if success:
        word_data = response.json()
        print(f"    Added word: {word_data['word']['word']} by {word_data['word']['added_by']}")
    
    # Test 7: Try adding duplicate word (should fail gracefully)
    print_step(7, "Testing duplicate word addition")
    response = requests.post(
        f"{SERVICE_URL}/word-admin/add-word",
        headers={"Authorization": f"Bearer {player1_token}"},
        json={"word": "TESTWORD", "language": "en"}
    )
    expected_conflict = response.status_code == 409
    print_result(expected_conflict, f"Duplicate word properly rejected: {response.status_code}")
    
    # Test 8: Add multiple words
    print_step(8, "Adding multiple words")
    test_words = ["WORDTEST", "TESTING", "WORDBATTLE", "SCRABBLE"]
    response = requests.post(
        f"{SERVICE_URL}/word-admin/add-words",
        headers={"Authorization": f"Bearer {player1_token}"},
        json={"words": test_words, "language": "en"}
    )
    success = response.status_code == 200
    print_result(success, f"Multiple word addition: {response.status_code}")
    if success:
        result = response.json()
        print(f"    Requested: {result['total_requested']}, Added: {result['newly_added']}, Existing: {result['already_existing']}")
    
    # Test 9: Get wordlist statistics
    print_step(9, "Getting wordlist statistics")
    response = requests.get(
        f"{SERVICE_URL}/word-admin/wordlist-stats",
        headers={"Authorization": f"Bearer {player1_token}"}
    )
    success = response.status_code == 200
    print_result(success, f"Statistics retrieval: {response.status_code}")
    if success:
        stats = response.json()
        print(f"    Languages: {len(stats['language_stats'])}")
        if stats['language_stats']:
            for lang_stat in stats['language_stats']:
                print(f"    {lang_stat['language']}: {lang_stat['total_words']} total, {lang_stat['user_added']} user-added")
        if stats['top_contributors']:
            print(f"    Top contributor: {stats['top_contributors'][0]['username']} ({stats['top_contributors'][0]['words_added']} words)")
    
    # Test 10: Download wordlist (text format)
    print_step(10, "Downloading wordlist (text format)")
    response = requests.get(
        f"{SERVICE_URL}/word-admin/download-wordlist/en?format=txt",
        headers={"Authorization": f"Bearer {player1_token}"}
    )
    success = response.status_code == 200
    print_result(success, f"Text download: {response.status_code}")
    if success:
        content = response.text
        lines = content.strip().split('\n')
        print(f"    Downloaded {len(lines)} words")
        # Check if our test words are in there
        test_words_found = sum(1 for word in ["TESTWORD", "WORDTEST"] if word in content)
        print(f"    Test words found: {test_words_found}/2")
    
    # Test 11: Download wordlist (CSV format)
    print_step(11, "Downloading wordlist (CSV format)")
    response = requests.get(
        f"{SERVICE_URL}/word-admin/download-wordlist/en?format=csv",
        headers={"Authorization": f"Bearer {player1_token}"}
    )
    success = response.status_code == 200
    print_result(success, f"CSV download: {response.status_code}")
    if success:
        content = response.text
        lines = content.strip().split('\n')
        print(f"    Downloaded CSV with {len(lines)} lines (including header)")
        # Check header
        if lines and "Word,Added By,Added Date" in lines[0]:
            print("    ✅ CSV header is correct")
        else:
            print("    ❌ CSV header is incorrect")
    
    # Test 12: List word admins (admin only)
    print_step(12, "Listing word admins")
    response = requests.get(
        f"{SERVICE_URL}/word-admin/list-word-admins",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    success = response.status_code == 200
    print_result(success, f"Word admin list: {response.status_code}")
    if success:
        admins = response.json()
        print(f"    Total word admins: {admins['total_count']}")
        for admin in admins['word_admins']:
            print(f"    - {admin['username']} (ID: {admin['id']})")
    
    # Test 13: Revoke word admin privileges
    print_step(13, "Revoking word admin privileges")
    response = requests.post(
        f"{SERVICE_URL}/word-admin/grant-word-admin",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"user_id": player1_user_id, "is_word_admin": False}
    )
    success = response.status_code == 200
    print_result(success, f"Privilege revocation: {response.status_code}")
    if success:
        print(f"    Response: {response.json()['message']}")
    
    # Test 14: Verify privilege revocation
    print_step(14, "Verifying privilege revocation")
    response = requests.get(
        f"{SERVICE_URL}/word-admin/status", 
        headers={"Authorization": f"Bearer {player1_token}"}
    )
    if response.status_code == 200:
        status_data = response.json()
        is_word_admin = status_data.get("is_word_admin", False)
        can_manage = status_data.get("can_manage_words", False)
        print_result(not is_word_admin and not can_manage, f"Privileges revoked: word_admin={is_word_admin}, can_manage={can_manage}")
    else:
        print_result(False, f"Failed to verify revocation: {response.status_code}")
    
    # Test 15: Confirm word addition is blocked again
    print_step(15, "Confirming word addition is blocked after revocation")
    response = requests.post(
        f"{SERVICE_URL}/word-admin/add-word",
        headers={"Authorization": f"Bearer {player1_token}"},
        json={"word": "BLOCKED", "language": "en"}
    )
    expected_failure = response.status_code == 403
    print_result(expected_failure, f"Post-revocation word addition properly blocked: {response.status_code}")
    
    print("\n" + "="*70)
    print("🎉 WORD ADMIN SYSTEM TEST COMPLETED!")
    print("="*70)
    
    return True

if __name__ == "__main__":
    try:
        success = test_word_admin_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        sys.exit(1) 