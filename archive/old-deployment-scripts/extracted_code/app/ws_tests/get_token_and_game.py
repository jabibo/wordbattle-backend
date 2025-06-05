# get_token_and_game.py
import requests
import json

# Register a user (if needed)
username = "wstest_user"
password = "testpassword"

register_response = requests.post(
    "http://localhost:8000/users/register",
    json={"username": username, "password": password}
)
print(f"Register response: {register_response.status_code}")

# Get token
token_response = requests.post(
    "http://localhost:8000/auth/token",
    data={"username": username, "password": password}
)
print(f"Token response: {token_response.status_code}")

if token_response.status_code == 200:
    token_data = token_response.json()
    token = token_data["access_token"]
    print(f"Token: {token}")
    
    # Create a game
    headers = {"Authorization": f"Bearer {token}"}
    game_response = requests.post(
        "http://localhost:8000/games/",
        headers=headers
    )
    print(f"Game creation response: {game_response.status_code}")
    
    if game_response.status_code == 200:
        game_data = game_response.json()
        game_id = game_data["id"]
        print(f"Game ID: {game_id}")
        
        # Join the game
        join_response = requests.post(
            f"http://localhost:8000/games/{game_id}/join",
            headers=headers
        )
        print(f"Join game response: {join_response.status_code}")
        
        # Save token and game ID for WebSocket test
        with open("ws_test_data.txt", "w") as f:
            f.write(f"{game_id}\n{token}")
        
        print("\nTest data saved to ws_test_data.txt")
        print(f"Run WebSocket test with: python ws_test.py {game_id} {token}")
