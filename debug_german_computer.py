#!/usr/bin/env python3
"""
Debug German computer AI by making it the computer's turn and testing the move logic.
"""

import requests
import json

def debug_german_computer():
    base_url = 'https://wordbattle-backend-test-441752988736.europe-west1.run.app'
    
    # Get admin token
    print("🔧 Getting admin token...")
    admin_response = requests.post(f'{base_url}/admin/debug/simple-login?email=jan@binge.de')
    admin_token = admin_response.json()['access_token']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    print("✅ Got admin token")
    
    # Create a fresh German game to test
    print(f"\n🇩🇪 Creating fresh German game...")
    create_game_data = {
        "language": "de",
        "max_players": 2,
        "add_computer_player": True,
        "computer_difficulty": "medium"
    }
    
    create_response = requests.post(f'{base_url}/games/', headers=admin_headers, json=create_game_data)
    if create_response.status_code != 200:
        print(f"❌ Failed to create German game: {create_response.status_code}")
        return
    
    german_game_id = create_response.json().get('id')
    print(f"✅ Created German game: {german_game_id}")
    
    # Get game details
    game_response = requests.get(f'{base_url}/games/{german_game_id}', headers=admin_headers)
    game_data = game_response.json()
    
    # Find players
    computer_player = None
    human_player = None
    for player in game_data.get('players', []):
        if player.get('is_computer'):
            computer_player = player
        else:
            human_player = player
    
    print(f"🤖 German Computer rack: {computer_player.get('rack', [])}")
    print(f"👤 German Human rack: {human_player.get('rack', [])}")
    print(f"🎯 Current player: {game_data.get('current_player_id')}")
    print(f"🤖 Computer user ID: {computer_player.get('user_id')}")
    
    # Check who goes first
    is_computer_turn = str(game_data.get('current_player_id')) == str(computer_player.get('user_id'))
    print(f"🎮 Is computer's turn: {is_computer_turn}")
    
    if is_computer_turn:
        # Test computer move directly
        print(f"\n🎮 Testing computer move in fresh German game...")
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
                print(f"   🎉 GERMAN COMPUTER MADE A MOVE!")
            else:
                print(f"   ❌ German computer passed on first move")
        else:
            print(f"❌ Computer move failed: {computer_move_response.status_code}")
            print(f"   Error: {computer_move_response.text}")
    else:
        # Make human move first, then test computer
        print(f"\n👤 Making human move first in German game...")
        human_rack = human_player.get('rack', [])
        if len(human_rack) >= 2:
            move_data = [
                {"row": 7, "col": 7, "letter": human_rack[0]},
                {"row": 7, "col": 8, "letter": human_rack[1]}
            ]
            
            print(f"   Placing: {human_rack[0]}{human_rack[1]} at center...")
            human_move_response = requests.post(f'{base_url}/games/{german_game_id}/move', headers=admin_headers, json=move_data)
            
            if human_move_response.status_code == 200:
                print(f"   ✅ Human move successful")
                
                # Now test computer move
                print(f"\n🎮 Testing computer move after human move...")
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
                        print(f"   🎉 GERMAN COMPUTER MADE A MOVE!")
                    else:
                        print(f"   ❌ German computer passed after human move")
                else:
                    print(f"❌ Computer move failed: {computer_move_response.status_code}")
                    print(f"   Error: {computer_move_response.text}")
            else:
                print(f"   ❌ Human move failed: {human_move_response.status_code}")
                print(f"   Error: {human_move_response.text}")
    
    # Test some basic German words that should be makeable
    print(f"\n🔍 Testing specific German words with computer rack...")
    computer_rack = computer_player.get('rack', [])
    print(f"Computer rack: {computer_rack}")
    
    # Try to find simple German words that can be made with common letters
    test_words = []
    rack_letters = set(computer_rack)
    
    # Common German words with common letters
    possible_words = [
        "ART", "RAT", "TAR", "DAR", "AID", "DIA", "TIA", "DART", "RAID", "ARID"
    ]
    
    for word in possible_words:
        word_letters = set(word.upper())
        if word_letters.issubset(rack_letters):
            test_words.append(word.upper())
    
    print(f"Possible words from rack: {test_words}")
    
    # Check if German wordlist contains these words
    if test_words:
        print(f"\n📚 Testing if German wordlist contains these words...")
        validate_response = requests.post(f'{base_url}/games/{german_game_id}/validate_words', 
                                        headers=admin_headers, 
                                        json=test_words)
        
        if validate_response.status_code == 200:
            validation_result = validate_response.json()
            valid_words = validation_result.get('valid_words', [])
            invalid_words = validation_result.get('invalid_words', [])
            print(f"   Valid German words: {valid_words}")
            print(f"   Invalid German words: {invalid_words}")
        else:
            print(f"   ❌ Word validation failed: {validate_response.status_code}")
            print(f"   Error: {validate_response.text}")
    
    # Compare with English behavior
    print(f"\n🇺🇸 Creating English comparison game...")
    english_create_data = {
        "language": "en",
        "max_players": 2,
        "add_computer_player": True,
        "computer_difficulty": "medium"
    }
    
    english_create_response = requests.post(f'{base_url}/games/', headers=admin_headers, json=english_create_data)
    if english_create_response.status_code == 200:
        english_game_id = english_create_response.json().get('id')
        print(f"✅ Created English comparison game: {english_game_id}")
        
        # Get English game details
        english_game_response = requests.get(f'{base_url}/games/{english_game_id}', headers=admin_headers)
        english_game_data = english_game_response.json()
        
        # Find English computer player
        english_computer = None
        english_human = None
        for player in english_game_data.get('players', []):
            if player.get('is_computer'):
                english_computer = player
            else:
                english_human = player
        
        print(f"🤖 English Computer rack: {english_computer.get('rack', [])}")
        
        # Test English computer on first move
        english_is_computer_turn = str(english_game_data.get('current_player_id')) == str(english_computer.get('user_id'))
        
        if english_is_computer_turn:
            print(f"🎮 Testing English computer first move...")
            english_computer_move = requests.post(f'{base_url}/games/{english_game_id}/computer-move', headers=admin_headers)
            
            if english_computer_move.status_code == 200:
                english_result = english_computer_move.json()
                print(f"✅ English computer result:")
                print(f"   Type: {english_result.get('move', {}).get('type')}")
                
                if english_result.get('move', {}).get('type') == 'place_tiles':
                    word = english_result.get('move', {}).get('word')
                    score = english_result.get('move', {}).get('score')
                    print(f"   Word: {word}")
                    print(f"   Score: {score}")
                    print(f"   🎉 ENGLISH COMPUTER WORKS ON FIRST MOVE!")
                else:
                    print(f"   ❌ English computer also passed on first move")

if __name__ == "__main__":
    debug_german_computer() 