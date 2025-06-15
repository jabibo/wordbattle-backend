#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.computer_player import ComputerPlayer
from app.game_logic.game_state import GameState, Position, PlacedTile
from app.utils.wordlist_utils import load_wordlist
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_computer_player_simple_move():
    """Test computer player making a simple first move."""
    
    # Load dictionary
    dictionary = load_wordlist("de")
    wordlist = list(dictionary)
    
    # Create a simple board with one tile to test cross-word validation
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Place a single tile at center to test cross-word formation
    board[7][7] = {"letter": "T", "is_blank": False, "tile_id": "test1"}
    
    # Create computer player
    computer = ComputerPlayer("medium")
    
    # Test rack with letters that can form words
    rack = "AUSEILN"
    
    print(f"🔍 Testing computer player with rack: {rack}")
    print(f"🔍 Board has tile 'T' at center (7,7)")
    print(f"🔍 Dictionary size: {len(dictionary)} words")
    
    # Try to find moves
    possible_moves = computer._find_possible_moves(board, list(rack), wordlist, "de")
    
    print(f"🔍 Found {len(possible_moves)} possible moves")
    
    if possible_moves:
        for i, move in enumerate(possible_moves[:5]):  # Show first 5 moves
            print(f"  Move {i+1}: {move['word']} at {move['start_pos']} {move['direction']} - {move['score']} points")
    else:
        print("❌ No moves found!")
        
        # Let's test a specific word manually
        print("\n🔍 Testing specific word 'AUS' manually...")
        
        # Test placing AUS horizontally starting at (7,5) to connect with T at (7,7)
        test_word = "AUS"
        test_placements = computer._find_word_placements_on_board(board, test_word, list(rack), "de", wordlist)
        
        print(f"🔍 Found {len(test_placements)} placements for '{test_word}'")
        
        if not test_placements:
            # Let's try a simpler approach - place AUS at center
            print("\n🔍 Testing AUS at center position...")
            
            # Create game state for validation
            game_state = GameState("de")
            game_state.center_used = False  # First move
            
            # Try placing AUS horizontally at center
            tiles = [
                (Position(7, 7), PlacedTile("A")),
                (Position(7, 8), PlacedTile("U")),
                (Position(7, 9), PlacedTile("S"))
            ]
            
            is_valid, error_msg, words_formed = game_state.validate_word_placement(tiles, dictionary)
            print(f"🔍 Validation result: {is_valid}")
            if not is_valid:
                print(f"❌ Error: {error_msg}")
            else:
                print(f"✅ Words formed: {words_formed}")

if __name__ == "__main__":
    test_computer_player_simple_move() 