import requests
import json

def test_only_completed_games():
    """Test the new only_completed parameter for my-games endpoint"""
    print("🎮 Testing Only Completed Games Filter")
    print("=" * 50)
    
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
    
    # Test 1: Get all games (default behavior)
    print("\n2. Testing default behavior (all games)...")
    response = requests.get(
        f"{backend_url}/games/my-games", 
        headers=headers, 
        timeout=15
    )
    
    if response.status_code == 200:
        all_games = response.json()
        total_all = all_games.get("total_games", 0)
        completed_all = all_games.get("completed_games", 0)
        print(f"✅ All games: {total_all} total, {completed_all} completed")
    else:
        print(f"❌ Failed to get all games: {response.status_code}")
        return
    
    # Test 2: Get only completed games
    print("\n3. Testing only_completed=true...")
    response = requests.get(
        f"{backend_url}/games/my-games?only_completed=true", 
        headers=headers, 
        timeout=15
    )
    
    if response.status_code == 200:
        completed_games = response.json()
        total_completed = completed_games.get("total_games", 0)
        completed_count = completed_games.get("completed_games", 0)
        
        print(f"✅ Completed games only: {total_completed} total")
        print(f"   Expected: {completed_all}, Got: {total_completed}")
        
        # Verify all returned games are completed
        games = completed_games.get("games", [])
        non_completed = [g for g in games if g.get("status") != "completed"]
        
        if non_completed:
            print(f"❌ Found {len(non_completed)} non-completed games in results:")
            for game in non_completed:
                print(f"   - Game {game.get('id')}: {game.get('status')}")
        else:
            print(f"✅ All {len(games)} returned games are completed")
            
        # Show some details of completed games
        if games:
            print(f"\n📊 Sample completed games:")
            for i, game in enumerate(games[:3]):
                status = game.get("status")
                completed_at = game.get("completed_at", "N/A")
                players = game.get("players", [])
                user_score = game.get("user_score", 0)
                print(f"   {i+1}. Game {game.get('id')[:8]}... - Status: {status}")
                print(f"      Completed: {completed_at}")
                print(f"      Your score: {user_score}")
                print(f"      Players: {len(players)}")
                
            if len(games) > 3:
                print(f"   ... and {len(games) - 3} more completed games")
                
    else:
        print(f"❌ Failed to get completed games: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test 3: Get only completed games with explicit false
    print("\n4. Testing only_completed=false...")
    response = requests.get(
        f"{backend_url}/games/my-games?only_completed=false", 
        headers=headers, 
        timeout=15
    )
    
    if response.status_code == 200:
        false_games = response.json()
        total_false = false_games.get("total_games", 0)
        print(f"✅ Explicit false: {total_false} total")
        print(f"   Should match default behavior: {total_all} vs {total_false}")
        
        if total_false == total_all:
            print("✅ Explicit false matches default behavior")
        else:
            print("❌ Explicit false doesn't match default behavior")
    else:
        print(f"❌ Failed to get games with explicit false: {response.status_code}")

if __name__ == "__main__":
    test_only_completed_games() 