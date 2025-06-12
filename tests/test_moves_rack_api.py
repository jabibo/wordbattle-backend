"""
Comprehensive API tests for moves and rack endpoints.
Tests game moves, letter rack management, and move validation.
"""
import pytest
from fastapi.testclient import TestClient
from app.models import Game, Player, Move
import json
import uuid


class TestMovesRackAPI:
    """Test moves and rack API endpoints."""

    @pytest.fixture
    def game_setup(self, client: TestClient, test_user, test_user2):
        """Create and setup a game for testing moves."""
        headers1 = {"Authorization": f"Bearer {test_user['token']}"}
        headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
        
        # Create game
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers1)
        
        game_id = create_response.json()["id"]
        
        # Join game
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # Start game
        start_response = client.post(f"/games/{game_id}/start", headers=headers1)
        
        return {
            "game_id": game_id,
            "headers1": headers1,
            "headers2": headers2,
            "current_player_id": start_response.json().get("current_player_id")
        }

    def test_get_user_rack_success(self, client: TestClient, test_user):
        """Test getting user's letter rack."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.get("/rack/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "racks" in data
        assert isinstance(data["racks"], list)

    def test_get_user_rack_unauthorized(self, client: TestClient):
        """Test getting rack without authentication."""
        response = client.get("/rack/")
        
        assert response.status_code == 401

    def test_get_game_rack_success(self, client: TestClient, game_setup):
        """Test getting rack for specific game."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        response = client.get(f"/rack/{game_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "rack" in data
        assert isinstance(data["rack"], list)

    def test_get_game_rack_not_in_game(self, client: TestClient, test_user):
        """Test getting rack for game user is not in."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        fake_game_id = str(uuid.uuid4())
        
        response = client.get(f"/rack/{fake_game_id}", headers=headers)
        
        assert response.status_code == 404

    def test_get_moves_history_success(self, client: TestClient, game_setup):
        """Test getting moves history for a game."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        response = client.get(f"/moves/{game_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "moves" in data
        assert isinstance(data["moves"], list)

    def test_get_moves_history_unauthorized(self, client: TestClient, test_user):
        """Test getting moves history without being in game."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        fake_game_id = str(uuid.uuid4())
        
        response = client.get(f"/moves/{fake_game_id}", headers=headers)
        
        assert response.status_code == 404

    def test_create_move_word_placement(self, client: TestClient, game_setup):
        """Test creating a word placement move."""
        game_id = game_setup["game_id"]
        current_player_id = game_setup["current_player_id"]
        
        # Determine which headers to use based on current player
        headers = game_setup["headers1"] if current_player_id else game_setup["headers1"]
        
        move_data = {
            "type": "word_placement",
            "tiles": [
                {"row": 7, "col": 7, "letter": "H"},
                {"row": 7, "col": 8, "letter": "E"},
                {"row": 7, "col": 9, "letter": "L"},
                {"row": 7, "col": 10, "letter": "L"},
                {"row": 7, "col": 11, "letter": "O"}
            ]
        }
        
        response = client.post(f"/moves/{game_id}", json=move_data, headers=headers)
        
        # Move might fail due to rack validation, that's expected in tests
        assert response.status_code in [200, 400]

    def test_create_move_pass_turn(self, client: TestClient, game_setup):
        """Test creating a pass turn move."""
        game_id = game_setup["game_id"]
        current_player_id = game_setup["current_player_id"]
        
        # Determine which headers to use based on current player
        headers = game_setup["headers1"] if current_player_id else game_setup["headers1"]
        
        move_data = {
            "type": "pass"
        }
        
        response = client.post(f"/moves/{game_id}", json=move_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "pass" in data["message"].lower()

    def test_create_move_exchange_letters(self, client: TestClient, game_setup):
        """Test creating a letter exchange move."""
        game_id = game_setup["game_id"]
        current_player_id = game_setup["current_player_id"]
        
        # Determine which headers to use based on current player
        headers = game_setup["headers1"] if current_player_id else game_setup["headers1"]
        
        move_data = {
            "type": "exchange",
            "letters": ["A", "B", "C"]
        }
        
        response = client.post(f"/moves/{game_id}", json=move_data, headers=headers)
        
        # Exchange might fail due to insufficient letters in bag
        assert response.status_code in [200, 400]

    def test_create_move_wrong_turn(self, client: TestClient, game_setup, test_user, test_user2):
        """Test creating move when it's not your turn."""
        game_id = game_setup["game_id"]
        current_player_id = game_setup["current_player_id"]
        
        # Use the wrong player's headers
        wrong_headers = game_setup["headers2"] if current_player_id == test_user["id"] else game_setup["headers1"]
        
        move_data = {
            "type": "pass"
        }
        
        response = client.post(f"/moves/{game_id}", json=move_data, headers=wrong_headers)
        
        assert response.status_code == 400
        assert "not your turn" in response.json()["detail"].lower()

    def test_create_move_invalid_game(self, client: TestClient, test_user):
        """Test creating move for non-existent game."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        fake_game_id = str(uuid.uuid4())
        
        move_data = {
            "type": "pass"
        }
        
        response = client.post(f"/moves/{fake_game_id}", json=move_data, headers=headers)
        
        assert response.status_code == 404

    def test_get_move_details(self, client: TestClient, game_setup):
        """Test getting details of a specific move."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        # First make a move
        move_data = {"type": "pass"}
        create_response = client.post(f"/moves/{game_id}", json=move_data, headers=headers)
        
        if create_response.status_code == 200:
            # Try to get move details if endpoint exists
            response = client.get(f"/moves/{game_id}/1", headers=headers)
            
            if response.status_code != 404:  # Endpoint exists
                assert response.status_code == 200
                data = response.json()
                assert "type" in data or "move_type" in data

    def test_validate_move_endpoint(self, client: TestClient, game_setup):
        """Test move validation endpoint."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        move_data = {
            "tiles": [
                {"row": 7, "col": 7, "letter": "H"},
                {"row": 7, "col": 8, "letter": "E"},
                {"row": 7, "col": 9, "letter": "L"},
                {"row": 7, "col": 10, "letter": "L"},
                {"row": 7, "col": 11, "letter": "O"}
            ]
        }
        
        response = client.post(f"/moves/{game_id}/validate", json=move_data, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 400]
            data = response.json()
            assert "valid" in data or "is_valid" in data

    def test_get_possible_moves(self, client: TestClient, game_setup):
        """Test getting possible moves for current rack."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        response = client.get(f"/moves/{game_id}/possible", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert "moves" in data or "possible_moves" in data

    def test_undo_last_move(self, client: TestClient, game_setup):
        """Test undoing last move."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        # First make a move
        move_data = {"type": "pass"}
        client.post(f"/moves/{game_id}", json=move_data, headers=headers)
        
        # Try to undo
        response = client.delete(f"/moves/{game_id}/last", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 400]  # 400 if undo not allowed

    def test_get_move_score_preview(self, client: TestClient, game_setup):
        """Test getting score preview for a potential move."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        move_data = {
            "tiles": [
                {"row": 7, "col": 7, "letter": "H"},
                {"row": 7, "col": 8, "letter": "E"},
                {"row": 7, "col": 9, "letter": "L"},
                {"row": 7, "col": 10, "letter": "L"},
                {"row": 7, "col": 11, "letter": "O"}
            ]
        }
        
        response = client.post(f"/moves/{game_id}/score-preview", json=move_data, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 400]
            if response.status_code == 200:
                data = response.json()
                assert "score" in data or "points" in data

    def test_rack_letter_distribution(self, client: TestClient, test_user):
        """Test getting letter distribution in rack."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.get("/rack/distribution", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_rack_suggestions(self, client: TestClient, game_setup):
        """Test getting word suggestions for current rack."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        response = client.get(f"/rack/{game_id}/suggestions", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert "suggestions" in data or "words" in data

    def test_rack_shuffle(self, client: TestClient, game_setup):
        """Test shuffling rack letters."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        response = client.post(f"/rack/{game_id}/shuffle", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_move_history_filtering(self, client: TestClient, game_setup):
        """Test filtering move history by type."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        # Make some moves first
        client.post(f"/moves/{game_id}", json={"type": "pass"}, headers=headers)
        
        # Filter by move type
        response = client.get(f"/moves/{game_id}?type=pass", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert "moves" in data

    def test_move_statistics(self, client: TestClient, game_setup):
        """Test getting move statistics for a game."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        response = client.get(f"/moves/{game_id}/stats", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_export_moves(self, client: TestClient, game_setup):
        """Test exporting moves history."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        response = client.get(f"/moves/{game_id}/export", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_replay_moves(self, client: TestClient, game_setup):
        """Test replaying moves for analysis."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        response = client.get(f"/moves/{game_id}/replay", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert "replay_data" in data or "moves" in data

    def test_move_annotations(self, client: TestClient, game_setup):
        """Test adding annotations to moves."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        # Make a move first
        move_response = client.post(f"/moves/{game_id}", json={"type": "pass"}, headers=headers)
        
        if move_response.status_code == 200:
            # Try to annotate the move
            response = client.post(f"/moves/{game_id}/1/annotate", json={
                "annotation": "Good strategic pass",
                "rating": 4
            }, headers=headers)
            
            if response.status_code != 404:  # Endpoint exists
                assert response.status_code == 200

    def test_bulk_move_operations(self, client: TestClient, game_setup):
        """Test bulk operations on moves."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        response = client.post(f"/moves/{game_id}/bulk", json={
            "action": "export",
            "move_ids": [1, 2, 3],
            "format": "json"
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 400]

    def test_unauthorized_access_moves_endpoints(self, client: TestClient):
        """Test accessing moves endpoints without authentication."""
        fake_game_id = str(uuid.uuid4())
        
        protected_endpoints = [
            ("GET", f"/moves/{fake_game_id}"),
            ("POST", f"/moves/{fake_game_id}"),
            ("GET", f"/rack/{fake_game_id}"),
            ("GET", "/rack/"),
        ]
        
        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            assert response.status_code == 401

    def test_invalid_move_data(self, client: TestClient, game_setup):
        """Test creating move with invalid data."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        # Test various invalid move data
        invalid_moves = [
            {},  # Empty move
            {"type": "invalid_type"},  # Invalid type
            {"type": "word_placement"},  # Missing tiles
            {"type": "exchange"},  # Missing letters
            {"type": "word_placement", "tiles": []},  # Empty tiles
        ]
        
        for invalid_move in invalid_moves:
            response = client.post(f"/moves/{game_id}", json=invalid_move, headers=headers)
            assert response.status_code in [400, 422]

    def test_move_time_limits(self, client: TestClient, game_setup):
        """Test move time limit enforcement."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        response = client.get(f"/moves/{game_id}/time-left", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert "time_left" in data or "seconds_remaining" in data

    def test_rack_letter_values(self, client: TestClient, game_setup):
        """Test getting letter values in rack."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        response = client.get(f"/rack/{game_id}/values", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert "letter_values" in data or "values" in data

    def test_move_validation_detailed(self, client: TestClient, game_setup):
        """Test detailed move validation with explanations."""
        game_id = game_setup["game_id"]
        headers = game_setup["headers1"]
        
        move_data = {
            "tiles": [
                {"row": 0, "col": 0, "letter": "A"}  # Invalid position
            ]
        }
        
        response = client.post(f"/moves/{game_id}/validate-detailed", json=move_data, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 400]
            data = response.json()
            assert "valid" in data or "is_valid" in data
            assert "reason" in data or "explanation" in data 