"""
Test for Scrabble move validation connectivity bug fix.

This test verifies that the backend correctly validates moves where new tiles
are connected through existing board tiles, following proper Scrabble rules.
"""

from app.game_logic.game_state import GameState, Position, PlacedTile


def test_tiles_connected_through_existing_board_tiles():
    """
    Test that new tiles can be placed with gaps that are filled by existing board tiles.
    
    This reproduces the bug scenario:
    - Existing tile A at (7,7) from previous word "RAD"
    - Player places G at (6,7) and R at (8,7)
    - Should form valid word "GAR" vertically: G-A-R
    - Backend should accept this move (previously rejected with "All tiles must be connected")
    """
    # Create a game state
    game_state = GameState("en")
    
    # Set up a board with an existing word "RAD" horizontally
    # R at (7,6), A at (7,7), D at (7,8)
    game_state.board[7][6] = PlacedTile("R")
    game_state.board[7][7] = PlacedTile("A") 
    game_state.board[7][8] = PlacedTile("D")
    game_state.center_used = True  # Mark center as used
    
    # Now try to place G at (6,7) and R at (8,7) to form "GAR" vertically
    # This uses the existing A at (7,7) to connect G and R
    word_positions = [
        (Position(6, 7), PlacedTile("G")),  # G above the A
        (Position(8, 7), PlacedTile("R"))   # R below the A
    ]
    
    # Create a simple dictionary with valid words
    dictionary = {"GAR", "RAD", "GRAD"}  # Include words that could be formed
    
    # This should be valid - the A at (7,7) connects G and R
    is_valid, error_message = game_state.validate_word_placement(word_positions, dictionary)
    
    assert is_valid, f"Move should be valid but got error: {error_message}"


def test_tiles_not_connected_without_existing_tiles():
    """
    Test that tiles are properly rejected when they're not connected and there are no existing tiles to connect them.
    """
    # Create a game state
    game_state = GameState("en")
    game_state.center_used = True  # Mark center as used
    
    # Try to place G at (6,8) and R at (8,8) with no connecting tile
    word_positions = [
        (Position(6, 8), PlacedTile("G")),
        (Position(8, 8), PlacedTile("R"))
    ]
    
    dictionary = {"GAR"}
    
    # This should be invalid - no existing tile connects G and R
    is_valid, error_message = game_state.validate_word_placement(word_positions, dictionary)
    
    assert not is_valid, "Move should be invalid when tiles are not connected"
    assert "connected" in error_message.lower(), f"Error should mention connectivity, got: {error_message}"


def test_horizontal_tiles_connected_through_existing_tiles():
    """
    Test horizontal placement where new tiles are connected through existing board tiles.
    """
    # Create a game state
    game_state = GameState("en")
    
    # Set up a board with an existing word "CAT" vertically
    # C at (6,7), A at (7,7), T at (8,7)
    game_state.board[6][7] = PlacedTile("C")
    game_state.board[7][7] = PlacedTile("A")
    game_state.board[8][7] = PlacedTile("T")
    game_state.center_used = True
    
    # Now try to place R at (7,6) and T at (7,8) to form "RAT" horizontally
    # This uses the existing A at (7,7) to connect R and T
    word_positions = [
        (Position(7, 6), PlacedTile("R")),  # R to the left of A
        (Position(7, 8), PlacedTile("T"))   # T to the right of A
    ]
    
    dictionary = {"RAT", "CAT"}
    
    # This should be valid - the A at (7,7) connects R and T
    is_valid, error_message = game_state.validate_word_placement(word_positions, dictionary)
    
    assert is_valid, f"Horizontal move should be valid but got error: {error_message}"


def test_multiple_gaps_filled_by_existing_tiles():
    """
    Test that multiple gaps can be filled by existing tiles.
    """
    # Create a game state
    game_state = GameState("en")
    
    # Set up existing tiles: S-P-A-R-E
    # S at (7,5), P at (7,6), A at (7,7), R at (7,8), E at (7,9)
    game_state.board[7][5] = PlacedTile("S")
    game_state.board[7][6] = PlacedTile("P")
    game_state.board[7][7] = PlacedTile("A")
    game_state.board[7][8] = PlacedTile("R")
    game_state.board[7][9] = PlacedTile("E")
    game_state.center_used = True
    
    # Now try to place D at (7,4) and D at (7,10) to form "DSPARED"
    # This uses multiple existing tiles to connect the new D's
    word_positions = [
        (Position(7, 4), PlacedTile("D")),  # D before SPARE
        (Position(7, 10), PlacedTile("D"))  # D after SPARE
    ]
    
    dictionary = {"DSPARED", "SPARE"}
    
    # This should be valid - existing tiles connect the D's
    is_valid, error_message = game_state.validate_word_placement(word_positions, dictionary)
    
    assert is_valid, f"Move with multiple gaps should be valid but got error: {error_message}"


def test_single_tile_placement_forms_multiple_words():
    """
    Test that single tile placement that forms multiple words is handled correctly.
    """
    # Create a game state
    game_state = GameState("en")
    
    # Set up existing words:
    # Horizontal: CAT at row 7, cols 6-8
    # Vertical: DOG at col 7, rows 5-7 (shares A with CAT)
    game_state.board[7][6] = PlacedTile("C")
    game_state.board[7][7] = PlacedTile("A")
    game_state.board[7][8] = PlacedTile("T")
    game_state.board[5][7] = PlacedTile("D")
    game_state.board[6][7] = PlacedTile("O")
    # A is already at (7,7)
    game_state.center_used = True
    
    # Place S at (8,7) to form "DOGS" vertically
    word_positions = [
        (Position(8, 7), PlacedTile("S"))
    ]
    
    dictionary = {"CAT", "DOG", "DOGS", "AS", "DOAS"}  # Include all possible words
    
    # This should be valid
    is_valid, error_message = game_state.validate_word_placement(word_positions, dictionary)
    
    assert is_valid, f"Single tile forming multiple words should be valid but got error: {error_message}"


if __name__ == "__main__":
    # Run the tests one by one to see which pass/fail
    tests = [
        ("Tiles connected through existing board tiles", test_tiles_connected_through_existing_board_tiles),
        ("Tiles not connected without existing tiles", test_tiles_not_connected_without_existing_tiles),
        ("Horizontal tiles connected through existing tiles", test_horizontal_tiles_connected_through_existing_tiles),
        ("Multiple gaps filled by existing tiles", test_multiple_gaps_filled_by_existing_tiles),
        ("Single tile placement forms multiple words", test_single_tile_placement_forms_multiple_words),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name}: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    if failed == 0:
        print("All tests passed!") 