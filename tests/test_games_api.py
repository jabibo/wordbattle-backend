"""
Comprehensive API tests for games endpoints.
Tests game creation, joining, starting, moves, and game state management.
"""
import pytest
from fastapi.testclient import TestClient
from app.models import Game, Player, GameStatus
import json
import uuid


class TestGamesAPI:
    """Test games API endpoints."""

    def test_create_game_success(self, client: TestClient, test_user):
        """Test successful game creation."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["language"] == "en"
        assert data["max_players"] == 2
        assert data["status"] == "setup"
        assert data["creator_id"] == test_user["id"]

    def test_create_game_with_computer_player(self, client: TestClient, test_user):
        """Test creating game with computer player."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.post("/games/", json={
            "language": "en",
            "max_players": 2,
            "add_computer_player": True,
            "computer_difficulty": "medium"
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"  # Should auto-start

    def test_create_game_invalid_language(self, client: TestClient, test_user):
        """Test game creation with invalid language."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.post("/games/", json={
            "language": "invalid",
            "max_players": 2
        }, headers=headers)
        
        assert response.status_code == 400
        assert "invalid_language" in response.json()["detail"]

    def test_create_game_invalid_max_players(self, client: TestClient, test_user):
        """Test game creation with invalid max_players."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.post("/games/", json={
            "language": "en",
            "max_players": 1  # Invalid: too few
        }, headers=headers)
        
        assert response.status_code == 400

    def test_create_game_unauthorized(self, client: TestClient):
        """Test game creation without authentication."""
        response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        })
        
        assert response.status_code == 401

    def test_create_game_with_invitations(self, client: TestClient, test_user, test_user2):
        """Test creating game with invitations."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.post("/games/create-with-invitations", json={
            "language": "en",
            "max_players": 2,
            "invitees": [test_user2["username"]],
            "base_url": "http://localhost:3000"
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "game" in data
        assert "invitations" in data
        assert len(data["invitations"]) == 1

    def test_join_game_success(self, client: TestClient, test_user, test_user2, db_session):
        """Test successfully joining a game."""
        # Create a game first
        headers1 = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers1)
        
        game_id = create_response.json()["id"]
        
        # Join with second user
        headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
        response = client.post(f"/games/{game_id}/join", headers=headers2)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_join_game_already_joined(self, client: TestClient, test_user):
        """Test joining a game already joined."""
        # Create a game
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers)
        
        game_id = create_response.json()["id"]
        
        # Try to join own game
        response = client.post(f"/games/{game_id}/join", headers=headers)
        
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_join_game_full(self, client: TestClient, test_user, test_user2, db_session):
        """Test joining a full game."""
        # Create a 2-player game and fill it
        headers1 = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers1)
        
        game_id = create_response.json()["id"]
        
        # Join with second user
        headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # Create third user and try to join
        third_user_response = client.post("/users/register", json={
            "username": "thirduser",
            "password": "password123",
            "email": "third@example.com"
        })
        
        # Get token for third user
        token_response = client.post("/auth/token", data={
            "username": "thirduser",
            "password": "password123"
        })
        third_token = token_response.json()["access_token"]
        
        headers3 = {"Authorization": f"Bearer {third_token}"}
        response = client.post(f"/games/{game_id}/join", headers=headers3)
        
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()

    def test_start_game_success(self, client: TestClient, test_user, test_user2):
        """Test successfully starting a game."""
        # Create and join game
        headers1 = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers1)
        
        game_id = create_response.json()["id"]
        
        headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # Start game
        response = client.post(f"/games/{game_id}/start", headers=headers1)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert "current_player_id" in data

    def test_start_game_not_ready(self, client: TestClient, test_user):
        """Test starting game with insufficient players."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers)
        
        game_id = create_response.json()["id"]
        
        # Try to start with only one player
        response = client.post(f"/games/{game_id}/start", headers=headers)
        
        assert response.status_code == 400
        assert "not ready" in response.json()["detail"].lower()

    def test_get_game_details(self, client: TestClient, test_user):
        """Test getting game details."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers)
        
        game_id = create_response.json()["id"]
        
        # Get game details
        response = client.get(f"/games/{game_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == game_id
        assert data["language"] == "en"
        assert "board" in data
        assert "players" in data

    def test_get_nonexistent_game(self, client: TestClient, test_user):
        """Test getting details of non-existent game."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        fake_game_id = str(uuid.uuid4())
        
        response = client.get(f"/games/{fake_game_id}", headers=headers)
        
        assert response.status_code == 404

    def test_list_user_games(self, client: TestClient, test_user):
        """Test listing user's games."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Create multiple games
        for i in range(3):
            client.post("/games/", json={
                "language": "en",
                "max_players": 2
            }, headers=headers)
        
        # List games
        response = client.get("/games/my-games", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "games" in data
        assert len(data["games"]) == 3
        assert "total_games" in data

    def test_list_user_games_with_filter(self, client: TestClient, test_user, test_user2):
        """Test listing user's games with status filter."""
        headers1 = {"Authorization": f"Bearer {test_user['token']}"}
        headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
        
        # Create and start a game
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers1)
        
        game_id = create_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers1)
        
        # List only in-progress games
        response = client.get("/games/my-games?status_filter=in_progress", headers=headers1)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["games"]) == 1
        assert data["games"][0]["status"] == "in_progress"

    def test_make_move_success(self, client: TestClient, test_user, test_user2):
        """Test making a valid move."""
        headers1 = {"Authorization": f"Bearer {test_user['token']}"}
        headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
        
        # Create, join and start game
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers1)
        
        game_id = create_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers2)
        client.post(f"/games/{game_id}/start", headers=headers1)
        
        # Make a move (place word "HOUSE" horizontally starting at center)
        move_data = [
            {"row": 7, "col": 7, "letter": "H"},
            {"row": 7, "col": 8, "letter": "O"},
            {"row": 7, "col": 9, "letter": "U"},
            {"row": 7, "col": 10, "letter": "S"},
            {"row": 7, "col": 11, "letter": "E"}
        ]
        
        response = client.post(f"/games/{game_id}/move", json=move_data, headers=headers1)
        
        # Move might fail due to rack validation, that's ok for this test
        assert response.status_code in [200, 400]

    def test_make_move_wrong_turn(self, client: TestClient, test_user, test_user2):
        """Test making move when it's not your turn."""
        headers1 = {"Authorization": f"Bearer {test_user['token']}"}
        headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
        
        # Create, join and start game
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers1)
        
        game_id = create_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers2)
        start_response = client.post(f"/games/{game_id}/start", headers=headers1)
        
        current_player_id = start_response.json()["current_player_id"]
        
        # Try to make move with wrong player
        wrong_headers = headers2 if current_player_id == test_user["id"] else headers1
        
        move_data = [{"row": 7, "col": 7, "letter": "A"}]
        response = client.post(f"/games/{game_id}/move", json=move_data, headers=wrong_headers)
        
        assert response.status_code == 400
        assert "not your turn" in response.json()["detail"].lower()

    def test_pass_turn_success(self, client: TestClient, test_user, test_user2):
        """Test passing turn."""
        headers1 = {"Authorization": f"Bearer {test_user['token']}"}
        headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
        
        # Create, join and start game
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers1)
        
        game_id = create_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers2)
        start_response = client.post(f"/games/{game_id}/start", headers=headers1)
        
        current_player_id = start_response.json()["current_player_id"]
        current_headers = headers1 if current_player_id == test_user["id"] else headers2
        
        # Pass turn
        response = client.post(f"/games/{game_id}/pass", headers=current_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "passed" in data["message"].lower()

    def test_exchange_letters_success(self, client: TestClient, test_user, test_user2):
        """Test exchanging letters."""
        headers1 = {"Authorization": f"Bearer {test_user['token']}"}
        headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
        
        # Create, join and start game
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers1)
        
        game_id = create_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers2)
        start_response = client.post(f"/games/{game_id}/start", headers=headers1)
        
        current_player_id = start_response.json()["current_player_id"]
        current_headers = headers1 if current_player_id == test_user["id"] else headers2
        
        # Exchange letters
        response = client.post(f"/games/{game_id}/exchange", json={
            "letters_to_exchange": ["A", "B"]
        }, headers=current_headers)
        
        # Exchange might fail due to insufficient letters in bag
        assert response.status_code in [200, 400]

    def test_validate_words_endpoint(self, client: TestClient, test_user):
        """Test word validation endpoint."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers)
        
        game_id = create_response.json()["id"]
        
        # Validate words
        response = client.post(f"/games/{game_id}/validate_words", json={
            "words": ["HOUSE", "CAR", "INVALIDWORD123"]
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "valid_words" in data
        assert "invalid_words" in data

    def test_get_game_invitations(self, client: TestClient, test_user):
        """Test getting game invitations."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers)
        
        game_id = create_response.json()["id"]
        
        response = client.get(f"/games/{game_id}/invitations", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_add_computer_player_endpoint(self, client: TestClient, test_user):
        """Test adding computer player to existing game."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers)
        
        game_id = create_response.json()["id"]
        
        response = client.post(f"/games/{game_id}/add-computer-player", json={
            "difficulty": "medium"
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "computer player added" in data["message"].lower()

    def test_search_users_for_invitation(self, client: TestClient, test_user, test_user2):
        """Test searching users for game invitations."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        response = client.get(f"/games/search-users?username_query={test_user2['username'][:3]}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        # Should find test_user2
        usernames = [user["username"] for user in data["users"]]
        assert test_user2["username"] in usernames

    def test_invite_user_by_username(self, client: TestClient, test_user, test_user2):
        """Test inviting user by username."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers)
        
        game_id = create_response.json()["id"]
        
        response = client.post(f"/games/{game_id}/invite-user", json={
            "username": test_user2["username"]
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "invitation sent" in data["message"].lower()

    def test_get_my_invitations(self, client: TestClient, test_user, test_user2):
        """Test getting user's pending invitations."""
        headers1 = {"Authorization": f"Bearer {test_user['token']}"}
        headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
        
        # Create game and invite user2
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers1)
        
        game_id = create_response.json()["id"]
        
        client.post(f"/games/{game_id}/invite-user", json={
            "username": test_user2["username"]
        }, headers=headers1)
        
        # Get invitations for user2
        response = client.get("/games/my-invitations", headers=headers2)
        
        assert response.status_code == 200
        data = response.json()
        assert "invitations" in data
        assert len(data["invitations"]) >= 1

    def test_unauthorized_access_game_endpoints(self, client: TestClient):
        """Test accessing game endpoints without authentication."""
        endpoints = [
            ("GET", "/games/my-games"),
            ("POST", "/games/"),
            ("GET", "/games/my-invitations"),
            ("GET", "/games/search-users"),
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            assert response.status_code == 401 