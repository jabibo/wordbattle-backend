import requests
import json
from urllib.parse import urlencode

def test_status_filter():
    """Test the new status_filter parameter for my-games endpoint"""
    print("🎮 Testing Status Filter for My-Games Endpoint")
    print("=" * 60)
    
    backend_url = "https://wordbattle-backend-441752988736.europe-west1.run.app"
    
    # Login first
    print("1. Logging in...")
    login_data = {
        "username": "aws_game_creator", 
        "password": "testpassword123"
    }
    
    response = requests.post(f"{backend_url}/auth/token", data=login_data, timeout=10)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token_data = response.json()
    access_token = token_data.get("access_token")
    print(f"✅ Login successful")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test 1: Default behavior (no filter)
    print("\n2. Testing default behavior (no status filter)...")
    response = requests.get(f"{backend_url}/games/my-games", headers=headers, timeout=15)
    
    if response.status_code == 200:
        all_games = response.json()
        total_all = all_games.get("total_games", 0)
        completed_all = all_games.get("completed_games", 0)
        active_all = all_games.get("active_games", 0)
        waiting_all = all_games.get("games_waiting_for_user", 0)
        
        print(f"✅ All games: {total_all} total")
        print(f"   - Completed: {completed_all}")
        print(f"   - Active: {active_all}")
        print(f"   - Waiting for user: {waiting_all}")
        
        # Get status breakdown
        games = all_games.get("games", [])
        status_counts = {}
        for game in games:
            status = game.get("status")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"   - Status breakdown: {status_counts}")
    else:
        print(f"❌ Failed to get all games: {response.status_code}")
        return
    
    # Test 2: Only completed games
    print("\n3. Testing status_filter=[completed]...")
    params = {"status_filter": ["completed"]}
    response = requests.get(f"{backend_url}/games/my-games", headers=headers, params=params, timeout=15)
    
    if response.status_code == 200:
        completed_games = response.json()
        test_filter_result("completed", completed_games, ["completed"])
    else:
        print(f"❌ Failed to get completed games: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test 3: Only active games (in_progress)
    print("\n4. Testing status_filter=[in_progress]...")
    params = {"status_filter": ["in_progress"]}
    response = requests.get(f"{backend_url}/games/my-games", headers=headers, params=params, timeout=15)
    
    if response.status_code == 200:
        active_games = response.json()
        test_filter_result("in_progress", active_games, ["in_progress"])
    else:
        print(f"❌ Failed to get active games: {response.status_code}")
    
    # Test 4: Multiple statuses (completed + in_progress)
    print("\n5. Testing status_filter=[completed,in_progress]...")
    params = {"status_filter": ["completed", "in_progress"]}
    response = requests.get(f"{backend_url}/games/my-games", headers=headers, params=params, timeout=15)
    
    if response.status_code == 200:
        multi_status_games = response.json()
        test_filter_result("completed+in_progress", multi_status_games, ["completed", "in_progress"])
    else:
        print(f"❌ Failed to get multi-status games: {response.status_code}")
    
    # Test 5: All possible statuses explicitly
    print("\n6. Testing status_filter=[setup,ready,in_progress,completed,cancelled]...")
    params = {"status_filter": ["setup", "ready", "in_progress", "completed", "cancelled"]}
    response = requests.get(f"{backend_url}/games/my-games", headers=headers, params=params, timeout=15)
    
    if response.status_code == 200:
        all_explicit_games = response.json()
        total_explicit = all_explicit_games.get("total_games", 0)
        print(f"✅ All statuses explicit: {total_explicit} total")
        print(f"   Should match default behavior: {total_all} vs {total_explicit}")
        
        if total_explicit == total_all:
            print("✅ Explicit all statuses matches default behavior")
        else:
            print("❌ Explicit all statuses doesn't match default behavior")
    else:
        print(f"❌ Failed to get all explicit games: {response.status_code}")
    
    # Test 6: Empty list (should show all)
    print("\n7. Testing empty status_filter=[]...")
    # Note: This might be tricky to test via URL params, so we'll test via direct API
    response = requests.get(f"{backend_url}/games/my-games?status_filter=", headers=headers, timeout=15)
    
    if response.status_code == 200:
        empty_filter_games = response.json()
        total_empty = empty_filter_games.get("total_games", 0)
        print(f"✅ Empty filter: {total_empty} total")
        print(f"   Should match default behavior: {total_all} vs {total_empty}")
        
        if total_empty == total_all:
            print("✅ Empty filter matches default behavior")
        else:
            print("❌ Empty filter doesn't match default behavior")
    else:
        print(f"❌ Failed to get empty filter games: {response.status_code}")
    
    # Test 7: Invalid status
    print("\n8. Testing invalid status_filter=[invalid_status]...")
    params = {"status_filter": ["invalid_status"]}
    response = requests.get(f"{backend_url}/games/my-games", headers=headers, params=params, timeout=15)
    
    if response.status_code == 400:
        print("✅ Invalid status correctly rejected with 400 error")
        try:
            error_data = response.json()
            print(f"   Error message: {error_data.get('detail', 'No detail')}")
        except:
            print(f"   Error response: {response.text}")
    else:
        print(f"❌ Invalid status should return 400, got: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("🎉 Status filter testing completed!")

def test_filter_result(test_name, result_data, expected_statuses):
    """Helper function to test filter results"""
    total = result_data.get("total_games", 0)
    games = result_data.get("games", [])
    
    print(f"✅ {test_name} filter: {total} total games")
    
    if total == 0:
        print(f"   No games found with status(es): {expected_statuses}")
        return
    
    # Verify all returned games have expected statuses
    unexpected_games = []
    status_counts = {}
    
    for game in games:
        status = game.get("status")
        status_counts[status] = status_counts.get(status, 0) + 1
        
        if status not in expected_statuses:
            unexpected_games.append((game.get("id", "unknown"), status))
    
    if unexpected_games:
        print(f"❌ Found {len(unexpected_games)} games with unexpected status:")
        for game_id, status in unexpected_games[:3]:  # Show first 3
            print(f"   - Game {game_id[:8]}...: {status}")
        if len(unexpected_games) > 3:
            print(f"   ... and {len(unexpected_games) - 3} more")
    else:
        print(f"✅ All {len(games)} games have expected status(es)")
        print(f"   Status breakdown: {status_counts}")
        
        # Show sample games
        if games:
            print(f"   Sample games:")
            for i, game in enumerate(games[:2]):
                status = game.get("status")
                game_id = game.get("id", "unknown")[:8]
                user_score = game.get("user_score", 0)
                print(f"   {i+1}. Game {game_id}... - Status: {status}, Your score: {user_score}")

if __name__ == "__main__":
    test_status_filter() 