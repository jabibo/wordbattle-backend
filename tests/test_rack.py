import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Game, User, Player
from app.game_logic.letter_bag import LETTER_DISTRIBUTION
import json

@pytest.fixture
def test_game_with_player(db_session, test_user):
    """Create a test game with a player."""
    # Create game
    game = Game(
        id="test-game-id",
        creator_id=test_user["id"],
        state=json.dumps({
            "board": [[None]*15 for _ in range(15)],
            "language": "de",
            "phase": "in_progress"
        })
    )
    db_session.add(game)
    
    # Add player
    player = Player(
        game_id=game.id,
        user_id=test_user["id"],
        rack="ABCDEF"  # 6 letters, one short of full rack
    )
    db_session.add(player)
    
    db_session.commit()
    return game, player

def test_get_all_racks(authenticated_client, test_game_with_player):
    """Test getting all racks for a user."""
    response = authenticated_client.get("/rack/")
    assert response.status_code == 200
    assert "racks" in response.json()

def test_get_game_rack(authenticated_client, test_game_with_player):
    """Test getting rack for a specific game."""
    game, _ = test_game_with_player
    response = authenticated_client.get(f"/rack/{game.id}")
    assert response.status_code == 200
    assert "rack" in response.json()

def test_get_nonexistent_game_rack(authenticated_client):
    """Test getting rack for a non-existent game."""
    response = authenticated_client.get("/rack/nonexistent-game")
    assert response.status_code == 404

def test_refill_rack(authenticated_client, test_game_with_player):
    """Test refilling a rack."""
    game, player = test_game_with_player
    response = authenticated_client.post(f"/rack/{game.id}/refill")
    assert response.status_code == 200
    assert "new_rack" in response.json()

def test_refill_full_rack(authenticated_client, db_session, test_game_with_player):
    """Test attempting to refill an already full rack."""
    game, player = test_game_with_player

    # First make the rack full
    player.rack = "ABCDEFG"
    db_session.commit()

    response = authenticated_client.post(f"/rack/{game.id}/refill")
    assert response.status_code == 200
    assert response.json()["new_rack"] == "ABCDEFG"  # Should remain unchanged

def test_refill_multiple_letters(authenticated_client, db_session, test_game_with_player):
    """Test refilling multiple letters."""
    game, player = test_game_with_player

    # Set rack to have only 4 letters
    player.rack = "ABCD"
    db_session.commit()

    response = authenticated_client.post(f"/rack/{game.id}/refill")
    assert response.status_code == 200
    assert len(response.json()["new_rack"]) == 7  # Should be filled to 7 letters

def test_refill_unauthorized(authenticated_client, test_game_with_player):
    """Test refilling rack for unauthorized user."""
    game, _ = test_game_with_player
    
    # Create a new client without auth
    client = TestClient(app)
    response = client.post(f"/rack/{game.id}/refill")
    assert response.status_code == 401  # Unauthorized 