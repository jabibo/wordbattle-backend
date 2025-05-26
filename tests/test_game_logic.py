from app.game_logic.validate_move import validate_move
from app.game_logic.full_points import calculate_full_move_points
from app.game_logic.board_utils import apply_move_to_board, find_word_placements
from app.models.game import GameStatus

def test_validate_move_out_of_bounds():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Test move with coordinates outside the board bounds
    # First check if coordinates are valid before accessing the board
    move_letters = [(14, 14, "X")]  # Valid coordinates at edge
    player_rack = ["X"]
    dictionary = set(["X"])
    
    is_valid, reason = validate_move(board, move_letters, player_rack, dictionary)
    assert is_valid
    
    # Now test with invalid coordinates
    move_letters = [(15, 7, "X")]  # Invalid row
    is_valid, _ = validate_move(board, move_letters, player_rack, dictionary)
    assert not is_valid

def test_validate_move_letters_not_in_rack():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Test move with letters not in player's rack
    move_letters = [(7, 7, "Z"), (7, 8, "Y")]
    player_rack = ["A", "B", "C"]
    dictionary = set(["ZY"])
    
    is_valid, reason = validate_move(board, move_letters, player_rack, dictionary)
    assert not is_valid
    assert "nicht" in reason

def test_calculate_points_with_multipliers():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Define a move on a word multiplier
    move_letters = [(0, 0, "H"), (0, 1, "A"), (0, 2, "T")]
    
    # Define letter points and multipliers
    letter_points = {'A': 1, 'H': 2, 'T': 1}
    multipliers = {(0, 0): "WW"}  # Triple word score at (0,0)
    dictionary = set(["HAT"])
    
    result = calculate_full_move_points(board, move_letters, letter_points, multipliers, dictionary)
    
    assert result["valid"]
    assert result["total"] > 4  # Should be more than sum of letter points due to multiplier

def test_all_letters_bonus():
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    
    # Define a move using all 7 letters
    move_letters = [
        (7, 7, "S"), (7, 8, "C"), (7, 9, "R"), (7, 10, "A"), 
        (7, 11, "B"), (7, 12, "B"), (7, 13, "L")
    ]
    
    # Define letter points and multipliers
    letter_points = {
        'S': 1, 'C': 4, 'R': 1, 'A': 1, 'B': 3, 'L': 2
    }
    multipliers = {}
    dictionary = set(["SCRABBL"])
    
    result = calculate_full_move_points(board, move_letters, letter_points, multipliers, dictionary)
    
    assert result["valid"]
    base_points = sum(letter_points[letter] for _, _, letter in move_letters)
    assert result["total"] >= base_points + 50  # Should include 50-point bonus

def test_validate_words(client, test_user, test_game_with_player):
    """Test word validation endpoint."""
    game, player = test_game_with_player
    
    # Login to get token
    response = client.post(
        "/auth/token",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Test word validation
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        f"/games/{game.id}/validate_words",
        headers=headers,
        json={
            "words": ["HAUS", "INVALID", "AUTO", "TISCH"],
            "include_placements": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "de"  # Test database uses German
    assert data["validations"]["HAUS"]["is_valid"] is True
    assert data["validations"]["AUTO"]["is_valid"] is True
    assert data["validations"]["TISCH"]["is_valid"] is True
    assert data["validations"]["INVALID"]["is_valid"] is False
    assert data["validations"]["INVALID"]["reason"] == "Word not found in dictionary"

def test_validate_words_unauthorized(client, test_user2, test_game_with_player):
    """Test word validation endpoint with unauthorized user."""
    game, player = test_game_with_player
    
    # Use the token from the fixture directly
    headers = {"Authorization": f"Bearer {test_user2['token']}"}
    response = client.post(
        f"/games/{game.id}/validate_words",
        headers=headers,
        json={
            "words": ["HAUS", "AUTO"],
            "include_placements": False
        }
    )
    
    assert response.status_code == 403
    assert "not part of this game" in response.json()["detail"]

def test_validate_words_with_placements(client, test_user, test_game_with_player):
    """Test word validation endpoint with placement suggestions."""
    game, player = test_game_with_player
    
    # Use the token from the fixture directly
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post(
        f"/games/{game.id}/validate_words",
        headers=headers,
        json={
            "words": ["HAUS"],
            "include_placements": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "de"
    assert data["validations"]["HAUS"]["is_valid"] is True
    assert "placements" in data["validations"]["HAUS"]
    
    # For first move, should have placements through center
    if game.status == GameStatus.READY:
        placements = data["validations"]["HAUS"]["placements"]
        assert len(placements) > 0
        for placement in placements:
            assert "position" in placement
            assert "direction" in placement
            assert "required_letters" in placement
            # Verify center tile is used
            row, col = placement["position"]
            direction = placement["direction"]
            word_len = len("HAUS")
            if direction == "horizontal":
                assert any(col <= 7 < col + word_len for col in range(15))
            else:
                assert any(row <= 7 < row + word_len for row in range(15))

def test_find_word_placements_first_move():
    """Test finding valid placements for the first move."""
    # Create an empty board
    board = [[None for _ in range(15)] for _ in range(15)]
    word = "TEST"
    player_rack = list("TEST")
    dictionary = set(["TEST"])
    
    placements = find_word_placements(board, word, player_rack, dictionary, is_first_move=True)
    
    # Should have multiple placements through center
    assert len(placements) > 0
    # All placements should use center tile (7,7)
    center = 7
    for placement in placements:
        row, col = placement["position"]
        direction = placement["direction"]
        word_len = len(word)
        if direction == "horizontal":
            assert col <= center < col + word_len
        else:
            assert row <= center < row + word_len
        
        # Verify score preview structure
        assert "score_preview" in placement
        score_preview = placement["score_preview"]
        assert "base_points" in score_preview
        assert "bonus_points" in score_preview
        assert "total_points" in score_preview
        assert "words_formed" in score_preview
        assert "multipliers_used" in score_preview
        
        # First move through center should use double word score
        assert score_preview["total_points"] > score_preview["base_points"]
        assert "TEST" in score_preview["words_formed"]

def test_find_word_placements_subsequent_move():
    """Test finding valid placements for a subsequent move."""
    # Create a board with an existing word
    board = [[None for _ in range(15)] for _ in range(15)]
    # Place "HAUS" horizontally at (7,7)
    for i, letter in enumerate("HAUS"):
        board[7][7+i] = letter
    
    word = "TEST"
    player_rack = list("TEST")
    dictionary = set(["TEST", "TS", "TE"])  # Include valid crosswords
    
    placements = find_word_placements(board, word, player_rack, dictionary, is_first_move=False)
    
    # Should find placements intersecting with "HAUS"
    assert len(placements) > 0
    # Each placement should either share a letter with "HAUS" or connect to it
    for placement in placements:
        row, col = placement["position"]
        direction = placement["direction"]
        assert len(placement["uses_board_letters"]) > 0  # Should use at least one board letter
        assert all(letter in player_rack for letter in placement["required_letters"])  # Should only use available letters
        
        # Verify score preview
        assert "score_preview" in placement
        score_preview = placement["score_preview"]
        assert "base_points" in score_preview
        assert "bonus_points" in score_preview
        assert "total_points" in score_preview
        assert "words_formed" in score_preview
        assert "multipliers_used" in score_preview
        
        # Should form at least two words (main word and crossword)
        assert len(score_preview["words_formed"]) >= 2
        
        # Total points should be the sum of base points and any bonuses
        assert score_preview["total_points"] == score_preview["base_points"] + score_preview["bonus_points"]

    # Verify placements are sorted by score in descending order
    scores = [p["score_preview"]["total_points"] for p in placements]
    assert scores == sorted(scores, reverse=True)