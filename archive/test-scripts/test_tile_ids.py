#!/usr/bin/env python3
"""
Test that tile IDs are properly preserved when storing and loading from database.
"""

import requests
import json
import time

# The deployed service URL
SERVICE_URL = "https://wordbattle-backend-441752988736.europe-west1.run.app"

def test_tile_id_persistence():
    """Test that tile IDs are preserved throughout the game flow."""
    print("=" * 70)
    print("TESTING TILE ID PERSISTENCE")
    print("=" * 70)
    
    # Get debug tokens
    response = requests.get(f"{SERVICE_URL}/debug/tokens")
    if response.status_code != 200:
        print("❌ Failed to get debug tokens")
        return False
    
    tokens_data = response.json()
    player1_token = tokens_data["tokens"]["player01"]["token"]
    player2_token = tokens_data["tokens"]["player02"]["token"]
    
    # Create a game
    headers1 = {"Authorization": f"Bearer {player1_token}", "Content-Type": "application/json"}
    headers2 = {"Authorization": f"Bearer {player2_token}", "Content-Type": "application/json"}
    
    create_response = requests.post(f"{SERVICE_URL}/games/", json={"language": "en", "max_players": 2}, headers=headers1)
    if create_response.status_code != 200:
        print(f"❌ Failed to create game: {create_response.status_code}")
        return False
    
    game_id = create_response.json()["id"]
    print(f"✅ Created game: {game_id}")
    
    # Join with player 2
    join_response = requests.post(f"{SERVICE_URL}/games/{game_id}/join", headers=headers2)
    if join_response.status_code != 200:
        print(f"❌ Failed to join game: {join_response.status_code}")
        return False
    
    # Start the game
    start_response = requests.post(f"{SERVICE_URL}/games/{game_id}/start", headers=headers1)
    if start_response.status_code != 200:
        print(f"❌ Failed to start game: {start_response.status_code}")
        return False
    
    print("✅ Game started successfully")
    
    # Get game state to see whose turn it is
    game_response = requests.get(f"{SERVICE_URL}/games/{game_id}", headers=headers1)
    if game_response.status_code != 200:
        print(f"❌ Failed to get game state: {game_response.status_code}")
        return False
    
    game_data = game_response.json()
    current_player_id = game_data["current_player_id"]
    current_headers = headers1 if current_player_id == 3 else headers2  # player01 has user_id 3, player02 has user_id 29
    
    print(f"✅ Current player: {current_player_id}")
    
    # Make a move with specific tile IDs
    custom_tile_ids = ["tile-123", "tile-456", "tile-789"]
    move_data = [
        {"row": 7, "col": 7, "letter": "C", "tile_id": custom_tile_ids[0]},  # Center
        {"row": 7, "col": 8, "letter": "A", "tile_id": custom_tile_ids[1]},
        {"row": 7, "col": 9, "letter": "T", "tile_id": custom_tile_ids[2]}
    ]
    
    print(f"🔍 Making move with custom tile IDs: {custom_tile_ids}")
    
    move_response = requests.post(f"{SERVICE_URL}/games/{game_id}/move", json=move_data, headers=current_headers)
    if move_response.status_code != 200:
        print(f"❌ Move failed: {move_response.status_code}")
        print(f"Error: {move_response.text}")
        return False
    
    print("✅ Move made successfully")
    
    # Get updated game state to check if tile IDs are preserved
    time.sleep(1)  # Brief pause to ensure state is updated
    updated_game_response = requests.get(f"{SERVICE_URL}/games/{game_id}", headers=headers1)
    if updated_game_response.status_code != 200:
        print(f"❌ Failed to get updated game state: {updated_game_response.status_code}")
        return False
    
    updated_game_data = updated_game_response.json()
    board = updated_game_data["board"]
    
    # Check if the tiles have the correct tile IDs
    tile_ids_found = []
    tiles_with_ids = []
    
    for row_idx, row in enumerate(board):
        for col_idx, cell in enumerate(row):
            if cell is not None:
                tile_id = cell.get("tile_id")
                if tile_id:
                    tile_ids_found.append(tile_id)
                    tiles_with_ids.append({
                        "position": f"({row_idx},{col_idx})", 
                        "letter": cell["letter"], 
                        "tile_id": tile_id
                    })
    
    print(f"\n🔍 Found {len(tiles_with_ids)} tiles on board:")
    for tile in tiles_with_ids:
        print(f"   {tile['letter']} at {tile['position']} with ID: {tile['tile_id']}")
    
    # Verify our custom tile IDs are preserved
    success = True
    for expected_id in custom_tile_ids:
        if expected_id in tile_ids_found:
            print(f"✅ Tile ID '{expected_id}' preserved correctly")
        else:
            print(f"❌ Tile ID '{expected_id}' was lost or changed")
            success = False
    
    # Check that all found tile IDs are our custom ones
    for found_id in tile_ids_found:
        if found_id not in custom_tile_ids:
            print(f"⚠️  Unexpected tile ID found: '{found_id}'")
    
    return success

def main():
    """Main test function."""
    success = test_tile_id_persistence()
    
    print(f"\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    
    if success:
        print("🎉 SUCCESS: Tile IDs are properly preserved in the database!")
        print("   ✅ Custom tile IDs maintained through move -> storage -> retrieval cycle")
    else:
        print("❌ FAILURE: Tile IDs are not being preserved correctly")
        print("   ❌ Custom tile IDs were lost or corrupted during database operations")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 