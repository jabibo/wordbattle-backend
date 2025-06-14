import requests
import json
import time

# Configuration - using Google Cloud Run
backend_url = "https://wordbattle-backend-skhco4fxoq-ew.a.run.app"

# Test credentials  
test_user = {
    "email": "test_list_games@example.com",
    "username": "test_game_lister",
    "password": "TestPassword123!",
    "remember_me": True
}

def test_list_games():
    """Test the new list games endpoint"""
    print("🎮 Testing List User Games Endpoint")
    print("=" * 50)
    
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
    
    # Test the list games endpoint
    print("\n2. Testing List Games Endpoint...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(
        f"{backend_url}/games/my-games", 
        headers=headers, 
        timeout=15
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            games_data = response.json()
            print(f"✅ Success! Games list retrieved")
            print(f"\nResponse structure:")
            print(json.dumps(games_data, indent=2))
            
            # Analyze the response
            games = games_data.get("games", [])
            total_games = games_data.get("total_games", 0)
            waiting_for_user = games_data.get("games_waiting_for_user", 0)
            active_games = games_data.get("active_games", 0)
            completed_games = games_data.get("completed_games", 0)
            
            print(f"\n📊 Games Summary:")
            print(f"   Total games: {total_games}")
            print(f"   Waiting for user: {waiting_for_user}")
            print(f"   Active games: {active_games}")
            print(f"   Completed games: {completed_games}")
            
            if games:
                print(f"\n🎯 Game Details:")
                for i, game in enumerate(games[:3]):  # Show first 3 games
                    print(f"\n   Game {i+1}:")
                    print(f"     ID: {game.get('id', 'N/A')}")
                    print(f"     Status: {game.get('status', 'N/A')}")
                    print(f"     Language: {game.get('language', 'N/A')}")
                    print(f"     Players: {game.get('current_players', 0)}/{game.get('max_players', 0)}")
                    print(f"     User's turn: {game.get('is_user_turn', False)}")
                    print(f"     User's score: {game.get('user_score', 0)}")
                    print(f"     Turn number: {game.get('turn_number', 0)}")
                    print(f"     Last activity: {game.get('time_since_last_activity', 'N/A')}")
                    
                    next_player = game.get('next_player')
                    if next_player:
                        print(f"     Next player: {next_player.get('username', 'N/A')} {'(YOU)' if next_player.get('is_current_user') else ''}")
                    
                    last_move = game.get('last_move')
                    if last_move:
                        print(f"     Last move: {last_move.get('description', 'N/A')} by {last_move.get('player_username', 'N/A')} {'(YOU)' if last_move.get('was_current_user') else ''}")
                    else:
                        print(f"     Last move: No moves yet")
                    
                    players = game.get('players', [])
                    if players:
                        print(f"     Players:")
                        for player in players:
                            creator_mark = " (Creator)" if player.get('is_creator') else ""
                            you_mark = " (YOU)" if player.get('is_current_user') else ""
                            print(f"       - {player.get('username', 'N/A')}: {player.get('score', 0)} points{creator_mark}{you_mark}")
                
                if len(games) > 3:
                    print(f"\n   ... and {len(games) - 3} more games")
            else:
                print(f"\n   No games found for this user")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print(f"Raw response: {response.text}")
    else:
        print(f"❌ Request failed with status {response.status_code}")
        print(f"Error response: {response.text}")

if __name__ == "__main__":
    test_list_games() 