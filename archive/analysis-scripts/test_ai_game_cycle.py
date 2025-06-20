#!/usr/bin/env python3
"""
Test AI/Computer Player Complete Game Cycle
Tests the full functionality of playing against AI with database connectivity
"""

import requests
import json
import time
import sys

# Base URL for the deployed API
BASE_URL = 'https://wordbattle-backend-test-441752988736.europe-west1.run.app'

def test_ai_game_cycle():
    print('🤖 Testing AI/Computer Player Complete Game Cycle')
    print('=' * 60)

    try:
        # Step 1: Register a human user
        print('👤 Step 1: Registering human user...')
        register_data = {
            'username': 'human_player_test',
            'email': 'human@test.com',
            'password': 'testpass123'
        }
        response = requests.post(f'{BASE_URL}/auth/register', json=register_data)
        print(f'   Registration status: {response.status_code}')
        if response.status_code != 200:
            print(f'   Error: {response.text}')
            return False

        # Step 2: Login to get token
        print('🔑 Step 2: Logging in...')
        login_data = {
            'email': 'human@test.com',
            'password': 'testpass123'
        }
        response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
        print(f'   Login status: {response.status_code}')
        if response.status_code != 200:
            print(f'   Error: {response.text}')
            return False

        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print('   ✅ Token obtained')

        # Step 3: Create a game against AI
        print('🎮 Step 3: Creating game against AI...')
        game_data = {
            'language': 'de',
            'rounds': 3,
            'opponent_type': 'computer'
        }
        response = requests.post(f'{BASE_URL}/games', json=game_data, headers=headers)
        print(f'   Game creation status: {response.status_code}')
        if response.status_code != 200:
            print(f'   Error: {response.text}')
            return False

        game_info = response.json()
        game_id = game_info['game_id']
        print(f'   ✅ Game created: {game_id}')
        print(f'   Players: {game_info.get("players", [])}')

        # Step 4: Get game status
        print('📊 Step 4: Checking initial game status...')
        response = requests.get(f'{BASE_URL}/games/{game_id}', headers=headers)
        print(f'   Status check: {response.status_code}')
        if response.status_code == 200:
            status = response.json()
            print(f'   Game status: {status.get("status", "unknown")}')
            print(f'   Round: {status.get("current_round", 0)}/{status.get("total_rounds", 0)}')
            print(f'   Players: {len(status.get("players", []))}')
        else:
            print(f'   Warning: Cannot get game status: {response.status_code}')

        # Step 5: Submit a word for human player
        print('📝 Step 5: Human player submitting word...')
        word_data = {
            'word': 'HAUS'
        }
        response = requests.post(f'{BASE_URL}/games/{game_id}/submit-word', json=word_data, headers=headers)
        print(f'   Word submission status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'   ✅ Word accepted: {result.get("word", "unknown")}')
            print(f'   Points: {result.get("points", 0)}')
        else:
            print(f'   Error submitting word: {response.text}')

        # Step 6: Wait for AI to play (if needed)
        print('🤖 Step 6: Waiting for AI response...')
        time.sleep(3)

        # Step 7: Check game status after AI move
        print('📊 Step 7: Checking game status after AI move...')
        response = requests.get(f'{BASE_URL}/games/{game_id}', headers=headers)
        if response.status_code == 200:
            status = response.json()
            print(f'   Game status: {status.get("status", "unknown")}')
            print(f'   Round: {status.get("current_round", 0)}/{status.get("total_rounds", 0)}')
            
            # Show player scores
            players = status.get('players', [])
            for player in players:
                print(f'   Player {player.get("username", "unknown")}: {player.get("score", 0)} points')
                
            # Show recent moves
            moves = status.get('moves', [])
            if moves:
                print('   Recent moves:')
                for move in moves[-4:]:  # Last 4 moves
                    print(f'     {move.get("player_username", "unknown")}: {move.get("word", "unknown")} ({move.get("points", 0)} pts)')
        else:
            print(f'   Error getting status: {response.status_code}')

        # Step 8: Test multiple rounds
        print('🔄 Step 8: Testing multiple rounds...')
        for round_num in range(2, 4):  # Rounds 2 and 3
            print(f'   Round {round_num}:')
            
            # Submit another word
            test_words = ['WELT', 'SPIEL']
            word_data = {'word': test_words[round_num - 2]}
            response = requests.post(f'{BASE_URL}/games/{game_id}/submit-word', json=word_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f'     ✅ Word submitted: {result.get("word", "unknown")} ({result.get("points", 0)} pts)')
            else:
                print(f'     ❌ Word submission failed: {response.status_code}')
            
            # Wait for AI
            time.sleep(2)
            
            # Check status
            response = requests.get(f'{BASE_URL}/games/{game_id}', headers=headers)
            if response.status_code == 200:
                status = response.json()
                print(f'     Status: {status.get("status", "unknown")} - Round {status.get("current_round", 0)}')

        # Step 9: Final game status
        print('🏁 Step 9: Final game results...')
        response = requests.get(f'{BASE_URL}/games/{game_id}', headers=headers)
        if response.status_code == 200:
            status = response.json()
            print(f'   Final status: {status.get("status", "unknown")}')
            
            players = status.get('players', [])
            print('   Final scores:')
            for player in players:
                username = player.get("username", "unknown")
                score = player.get("score", 0)
                print(f'     {username}: {score} points')
            
            # Determine winner
            if len(players) >= 2:
                sorted_players = sorted(players, key=lambda p: p.get("score", 0), reverse=True)
                winner = sorted_players[0]
                print(f'   🏆 Winner: {winner.get("username", "unknown")} with {winner.get("score", 0)} points')

        print('\n🎯 AI Game Cycle Test Complete!')
        return True

    except Exception as e:
        print(f'❌ Test failed with error: {str(e)}')
        return False

if __name__ == '__main__':
    success = test_ai_game_cycle()
    sys.exit(0 if success else 1) 