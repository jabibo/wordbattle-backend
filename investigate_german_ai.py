#!/usr/bin/env python3
"""
Investigate why computer AI is passing in German games but working in English games.
"""

import requests
import json

def investigate_german_ai():
    base_url = 'https://wordbattle-backend-test-441752988736.europe-west1.run.app'
    
    # Get admin token
    print("🔧 Getting admin token...")
    admin_response = requests.post(f'{base_url}/admin/debug/simple-login?email=jan@binge.de')
    if admin_response.status_code != 200:
        print(f"❌ Failed to get admin token: {admin_response.status_code}")
        return
    
    admin_token = admin_response.json()['access_token']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    print("✅ Got admin token")
    
    # Get the German game details
    german_game_id = "a7507fa1-bb7e-49a9-9fb6-c5b682a77df5"
    print(f"\n🇩🇪 Investigating German game: {german_game_id}")
    
    game_response = requests.get(f'{base_url}/admin/games/{german_game_id}', headers=admin_headers)
    if game_response.status_code != 200:
        print(f"❌ Failed to get game details: {game_response.status_code}")
        return
    
    game_data = game_response.json()
    print(f"✅ Got German game details")
    
    # Find computer player
    computer_player = None
    for player in game_data.get('players', []):
        if player.get('is_computer'):
            computer_player = player
            break
    
    if not computer_player:
        print("❌ No computer player found")
        return
    
    print(f"🤖 Computer Player in German game:")
    print(f"   Rack: {computer_player.get('rack', [])}")
    print(f"   Score: {computer_player.get('score', 0)}")
    print(f"   Current player ID: {game_data.get('current_player_id')}")
    print(f"   Computer user ID: {computer_player.get('user_id')}")
    
    # Check if it's computer's turn
    is_computer_turn = str(game_data.get('current_player_id')) == str(computer_player.get('user_id'))
    print(f"   Is computer's turn: {is_computer_turn}")
    
    # Get game state details
    game_state = game_data.get('game_state', {})
    print(f"\n📋 German Game State:")
    print(f"   Turn: {game_state.get('turn_number', 0)}")
    print(f"   Board tiles: {game_state.get('board_tiles', 0)}")
    print(f"   Consecutive passes: {game_state.get('consecutive_passes', 0)}")
    
    # Check recent moves to see the pattern
    recent_moves = game_data.get('recent_moves', [])
    print(f"\n📝 Recent moves in German game:")
    for move in recent_moves:
        move_type = move.get('move_type', 'unknown')
        player_name = move.get('player_username', 'Unknown')
        timestamp = move.get('timestamp', '')[:19]
        print(f"   {timestamp} - {player_name}: {move_type}")
    
    # Now test computer move if it's computer's turn
    if is_computer_turn:
        print(f"\n🎮 Testing computer move in German game...")
        computer_move_response = requests.post(f'{base_url}/games/{german_game_id}/computer-move', headers=admin_headers)
        
        if computer_move_response.status_code == 200:
            move_result = computer_move_response.json()
            print(f"✅ Computer move result:")
            print(f"   Type: {move_result.get('move', {}).get('type')}")
            print(f"   Message: {move_result.get('message')}")
            
            if move_result.get('move', {}).get('type') == 'place_tiles':
                word = move_result.get('move', {}).get('word')
                score = move_result.get('move', {}).get('score')
                tiles = move_result.get('move', {}).get('tiles', [])
                print(f"   Word: {word}")
                print(f"   Score: {score}")
                print(f"   Tiles: {len(tiles)} placed")
                print(f"   🎉 COMPUTER MADE A MOVE IN GERMAN!")
            else:
                print(f"   ❌ Computer passed again in German game")
        else:
            print(f"❌ Computer move failed: {computer_move_response.status_code}")
            print(f"   Error: {computer_move_response.text}")
    
    # Compare with English game behavior
    print(f"\n🇺🇸 Creating English test game for comparison...")
    create_game_data = {
        "language": "en",
        "max_players": 2,
        "add_computer_player": True,
        "computer_difficulty": "medium"
    }
    
    create_response = requests.post(f'{base_url}/games/', headers=admin_headers, json=create_game_data)
    if create_response.status_code == 200:
        english_game_id = create_response.json().get('id')
        print(f"✅ Created English test game: {english_game_id}")
        
        # Get English game details
        english_game_response = requests.get(f'{base_url}/games/{english_game_id}', headers=admin_headers)
        if english_game_response.status_code == 200:
            english_game_data = english_game_response.json()
            
            # Find computer player in English game
            english_computer = None
            english_human = None
            for player in english_game_data.get('players', []):
                if player.get('is_computer'):
                    english_computer = player
                else:
                    english_human = player
            
            if english_computer and english_human:
                print(f"🤖 English Computer rack: {english_computer.get('rack', [])}")
                print(f"👤 English Human rack: {english_human.get('rack', [])}")
                
                # Make a human move first
                human_rack = english_human.get('rack', [])
                if len(human_rack) >= 2:
                    move_data = [
                        {"row": 7, "col": 7, "letter": human_rack[0]},
                        {"row": 7, "col": 8, "letter": human_rack[1]}
                    ]
                    
                    print(f"Making human move in English: {human_rack[0]}{human_rack[1]} at center...")
                    human_move_response = requests.post(f'{base_url}/games/{english_game_id}/move', headers=admin_headers, json=move_data)
                    
                    if human_move_response.status_code == 200:
                        print(f"✅ Human move successful in English")
                        
                        # Test computer move in English
                        print(f"🎮 Testing computer move in English...")
                        english_computer_move = requests.post(f'{base_url}/games/{english_game_id}/computer-move', headers=admin_headers)
                        
                        if english_computer_move.status_code == 200:
                            english_result = english_computer_move.json()
                            print(f"✅ English computer move result:")
                            print(f"   Type: {english_result.get('move', {}).get('type')}")
                            
                            if english_result.get('move', {}).get('type') == 'place_tiles':
                                word = english_result.get('move', {}).get('word')
                                score = english_result.get('move', {}).get('score')
                                print(f"   Word: {word}")
                                print(f"   Score: {score}")
                                print(f"   🎉 ENGLISH COMPUTER WORKS!")
                            else:
                                print(f"   ❌ English computer also passed")
                        else:
                            print(f"❌ English computer move failed: {english_computer_move.status_code}")
    
    # Check German wordlist availability
    print(f"\n📚 Checking German wordlist...")
    wordlist_response = requests.get(f'{base_url}/admin/wordlists', headers=admin_headers)
    if wordlist_response.status_code == 200:
        wordlists = wordlist_response.json()
        print(f"✅ Available wordlists:")
        for wordlist in wordlists:
            language = wordlist.get('language')
            count = wordlist.get('word_count')
            print(f"   {language}: {count} words")
            
            if language == 'de':
                print(f"      🇩🇪 German wordlist available with {count} words")
            elif language == 'en':
                print(f"      🇺🇸 English wordlist available with {count} words")
    else:
        print(f"❌ Failed to get wordlists: {wordlist_response.status_code}")
    
    # Test word validation for German
    print(f"\n🔍 Testing German word validation...")
    test_german_words = ["HALLO", "WORT", "SPIEL", "HAUS", "AUTO"]
    
    for word in test_german_words:
        validate_response = requests.post(f'{base_url}/games/{german_game_id}/validate_words', 
                                        headers=admin_headers, 
                                        json=test_german_words[:1])  # Test one word at a time
        
        if validate_response.status_code == 200:
            validation_result = validate_response.json()
            valid_words = validation_result.get('valid_words', [])
            invalid_words = validation_result.get('invalid_words', [])
            print(f"   Tested: {test_german_words[:1]} - Valid: {len(valid_words)}, Invalid: {len(invalid_words)}")
            break  # Just test one to see if validation works
        else:
            print(f"   ❌ Word validation failed: {validate_response.status_code}")
            break

if __name__ == "__main__":
    investigate_german_ai() 