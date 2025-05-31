# make_move.py
import requests
import json
import sys
import random

def make_move(game_id, token):
    """Make a move in the game to trigger a WebSocket update."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # First, create a second player and join the game
    second_username = "wstest_user2"
    second_password = "testpassword"
    
    # Register second user
    register_response = requests.post(
        "http://localhost:8000/users/register",
        json={"username": second_username, "password": second_password}
    )
    print(f"Register second user response: {register_response.status_code}")
    
    # Get token for second user
    token_response = requests.post(
        "http://localhost:8000/auth/token",
        data={"username": second_username, "password": second_password}
    )
    print(f"Token for second user response: {token_response.status_code}")
    
    if token_response.status_code == 200:
        second_token = token_response.json()["access_token"]
        second_headers = {"Authorization": f"Bearer {second_token}"}
        
        # Join the game with second user
        join_response = requests.post(
            f"http://localhost:8000/games/{game_id}/join",
            headers=second_headers
        )
        print(f"Join game with second user response: {join_response.status_code}")
        
        # Start the game
        start_response = requests.post(
            f"http://localhost:8000/games/{game_id}/start",
            headers=headers
        )
        print(f"Start game response: {start_response.status_code}")
        
        # Get game state to see whose turn it is
        game_response = requests.get(f"http://localhost:8000/games/{game_id}")
        print(f"Get game state response: {game_response.status_code}")
        
        if game_response.status_code == 200:
            game_state = game_response.json()
            current_player_id = game_state.get("current_player_id")
            print(f"Current player ID: {current_player_id}")
            
            # Get user info to determine which token to use
            me_response = requests.get("http://localhost:8000/me", headers=headers)
            second_me_response = requests.get("http://localhost:8000/me", headers=second_headers)
            
            first_user_id = me_response.json().get("id") if me_response.status_code == 200 else None
            second_user_id = second_me_response.json().get("id") if second_me_response.status_code == 200 else None
            
            print(f"First user ID: {first_user_id}")
            print(f"Second user ID: {second_user_id}")
            
            # Determine which user's turn it is
            if current_player_id == first_user_id:
                active_headers = headers
                active_token = token
                print("It's the first user's turn")
            else:
                active_headers = second_headers
                active_token = second_token
                print("It's the second user's turn")
            
            # Deal letters to get rack for the active player
            deal_response = requests.post(
                f"http://localhost:8000/games/{game_id}/deal",
                headers=active_headers
            )
            print(f"Deal letters response: {deal_response.status_code}")
            
            if deal_response.status_code == 200:
                rack = deal_response.json().get("new_rack", "ABCDEFG")
                print(f"Player's rack: {rack}")
            else:
                # Use default letters
                rack = "ABCDEFG"
                print(f"Using default rack: {rack}")
            
            # Use letters from the rack
            available_letters = list(rack)
            if len(available_letters) < 5:
                print("Not enough letters in rack, using default letters")
                available_letters = ["A", "B", "C", "D", "E"]
            
            # Make a simple move with available letters
            move_data = {
                "move_data": [
                    {"row": 7, "col": 7, "letter": available_letters[0]},
                    {"row": 7, "col": 8, "letter": available_letters[1]},
                    {"row": 7, "col": 9, "letter": available_letters[2]},
                    {"row": 7, "col": 10, "letter": available_letters[3]},
                    {"row": 7, "col": 11, "letter": available_letters[4]}
                ]
            }
            
            move_response = requests.post(
                f"http://localhost:8000/games/{game_id}/move",
                headers=active_headers,
                json=move_data
            )
            
            print(f"Move response: {move_response.status_code}")
            if move_response.status_code == 200:
                print(json.dumps(move_response.json(), indent=2))
            else:
                print(move_response.text)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        # Try to read from file
        try:
            with open("ws_test_data.txt", "r") as f:
                lines = f.readlines()
                game_id = lines[0].strip()
                token = lines[1].strip()
        except:
            print("Usage: python make_move.py <game_id> <token>")
            sys.exit(1)
    else:
        game_id = sys.argv[1]
        token = sys.argv[2]
    
    make_move(game_id, token)
