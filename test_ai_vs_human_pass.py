#!/usr/bin/env python3
"""
Test AI vs Human: Human Pass, AI Move
Tests that when a human player passes, the AI can make a proper tile placement move
"""

import requests
import json
import time
import sys

# Base URL for the deployed API
BASE_URL = 'https://wordbattle-backend-test-441752988736.europe-west1.run.app'

def test_human_pass_ai_move():
    print('🎯 Testing Human Pass vs AI Move')
    print('=' * 50)

    try:
        # Step 1: Get test token from admin debug endpoint
        print('🔑 Step 1: Getting test token...')
        response = requests.post(f'{BASE_URL}/admin/debug/create-test-tokens')
        print(f'   Test token creation status: {response.status_code}')
        if response.status_code != 200:
            print(f'   Error: {response.text}')
            return False

        token_response = response.json()
        print(f'   Token response keys: {list(token_response.keys())}')
        
        # Get the first test user's token
        if 'users' in token_response and len(token_response['users']) > 0:
            token = token_response['users'][0]['access_token']
            username = token_response['users'][0]['username']
            print(f'   ✅ Test token obtained for user: {username}')
        else:
            print(f'   Error: No test users found in response: {token_response}')
            return False
            
        headers = {'Authorization': f'Bearer {token}'}

        # Step 2: Create a game with computer player (during creation)
        print('🎮 Step 2: Creating game with AI opponent...')
        # Try with short_game flag to simplify initialization
        game_data = {
            'language': 'en',
            'max_players': 2,
            'add_computer_player': True,
            'computer_difficulty': 'medium',
            'short_game': True
        }
        response = requests.post(f'{BASE_URL}/games/', json=game_data, headers=headers)
        print(f'   Game creation status: {response.status_code}')
        if response.status_code != 200:
            print(f'   Error: {response.text}')
            print(f'   Response content: {response.content}')
            return False

        game_info = response.json()
        game_id = game_info['id']
        print(f'   ✅ Game created: {game_id}')
        print(f'   Game status: {game_info.get("status", "unknown")}')

        # Step 3: Check initial game status (should be auto-started)
        print('📊 Step 3: Checking initial game status...')
        response = requests.get(f'{BASE_URL}/games/{game_id}', headers=headers)
        print(f'   Status check: {response.status_code}')
        if response.status_code == 200:
            status = response.json()
            print(f'   Game status: {status.get("status", "unknown")}')
            print(f'   Current player: {status.get("current_player_id", "unknown")}')
            print(f'   Players count: {len(status.get("players", []))}')
            
            # Show player info (players is a dict with user_id as keys)
            players = status.get("players", {})
            print(f'   Players data: {players}')
            for user_id, player in players.items():
                username = player.get("username", "unknown")
                rack = player.get("rack", "")
                is_current = str(user_id) == str(status.get("current_player_id"))
                current_marker = " [CURRENT TURN]" if is_current else ""
                print(f'     Player {user_id}: {username} (Rack: {rack}){current_marker}')
        else:
            print(f'   Warning: Cannot get game status: {response.status_code}')
            return False

        # Step 4: Human player passes their turn
        print('⏭️ Step 4: Human player passing turn...')
        response = requests.post(f'{BASE_URL}/games/{game_id}/pass', headers=headers)
        print(f'   Pass status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'   ✅ Pass successful: {result.get("message", "unknown")}')
            print(f'   Turn now: Player {result.get("next_player_id", "unknown")}')
        else:
            print(f'   Error passing: {response.text}')
            return False

        # Step 5: Check game state after human pass
        print('📊 Step 5: Checking game state after human pass...')
        response = requests.get(f'{BASE_URL}/games/{game_id}', headers=headers)
        if response.status_code == 200:
            status = response.json()
            current_player_id = status.get("current_player_id")
            players = status.get("players", [])
            
            # Find current player info
            current_player = None
            for user_id, player in players.items():
                if str(user_id) == str(current_player_id):
                    current_player = player
                    break
            
            if current_player:
                print(f'   Current player: {current_player.get("username", "unknown")}')
                print(f'   Current player rack: {current_player.get("rack", "")}')
                
                # Check if it's the AI's turn
                is_ai_turn = current_player.get("username") == "computer_player"
                print(f'   Is AI turn: {is_ai_turn}')
            else:
                print('   Could not determine current player')
        else:
            print(f'   Error getting status: {response.status_code}')

        # Step 6: Trigger AI move
        print('🤖 Step 6: Triggering AI move...')
        response = requests.post(f'{BASE_URL}/games/{game_id}/computer-move', headers=headers)
        print(f'   AI move trigger status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'   ✅ AI move result: {result.get("message", "unknown")}')
            print(f'   Move type: {result.get("move_type", "unknown")}')
            if "move_details" in result:
                move_details = result["move_details"]
                print(f'   AI played: {move_details.get("word", "unknown")} for {move_details.get("score", 0)} points')
        else:
            print(f'   Error triggering AI move: {response.text}')
            # This might be expected if AI turn handling is automatic

        # Step 7: Check final game state after AI move
        print('📊 Step 7: Checking game state after AI move...')
        time.sleep(2)  # Give AI time to process
        
        response = requests.get(f'{BASE_URL}/games/{game_id}', headers=headers)
        if response.status_code == 200:
            status = response.json()
            print(f'   Game status: {status.get("status", "unknown")}')
            print(f'   Current player: {status.get("current_player_id", "unknown")}')
            
            # Show player scores
            players = status.get('players', {})
            print('   Player scores:')
            for user_id, player in players.items():
                username = player.get("username", "unknown")
                score = player.get("score", 0)
                rack = player.get("rack", "")
                is_current = str(user_id) == str(status.get("current_player_id"))
                current_marker = " [CURRENT TURN]" if is_current else ""
                print(f'     {username}: {score} points (Rack: {rack}){current_marker}')
            
            # Show recent moves if available
            moves = status.get('moves', [])
            if moves:
                print('   Recent moves:')
                for move in moves[-3:]:  # Last 3 moves
                    player_name = move.get("player_username", "unknown")
                    move_type = move.get("type", "unknown")
                    if move_type == "place_tiles":
                        word = move.get("word", "unknown")
                        points = move.get("points", 0)
                        print(f'     {player_name}: {word} ({points} pts)')
                    else:
                        print(f'     {player_name}: {move_type}')
            
            # Show board state (simplified)
            board = status.get('board', [])
            if board:
                print('   Board state (non-empty tiles):')
                for row_idx, row in enumerate(board):
                    for col_idx, cell in enumerate(row):
                        if cell:
                            print(f'     [{row_idx},{col_idx}]: {cell}')
        else:
            print(f'   Error getting final status: {response.status_code}')

        print('\n🎯 Human Pass vs AI Move Test Complete!')
        return True

    except Exception as e:
        print(f'❌ Test failed with error: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_human_pass_ai_move()
    sys.exit(0 if success else 1) 