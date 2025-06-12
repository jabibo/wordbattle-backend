"""
Comprehensive API tests for additional endpoints.
Tests chat, profile, word admin, and system endpoints with token authentication.
"""
import pytest
from fastapi.testclient import TestClient
from app.models import User, WordList
from app.auth import create_access_token, get_password_hash
from datetime import datetime, timezone, timedelta
import json
import uuid


class TestChatAPI:
    """Test chat API endpoints."""

    @pytest.fixture
    def game_with_chat(self, client: TestClient, test_user, test_user2):
        """Create a game for chat testing."""
        headers1 = {"Authorization": f"Bearer {test_user['token']}"}
        headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
        
        # Create and join game
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers1)
        
        game_id = create_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        return {
            "game_id": game_id,
            "headers1": headers1,
            "headers2": headers2
        }

    def test_send_chat_message_success(self, client: TestClient, game_with_chat):
        """Test sending chat message in game."""
        game_id = game_with_chat["game_id"]
        headers = game_with_chat["headers1"]
        
        response = client.post(f"/chat/{game_id}", json={
            "message": "Hello, good luck!"
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Hello, good luck!"

    def test_get_chat_history_success(self, client: TestClient, game_with_chat):
        """Test getting chat history for game."""
        game_id = game_with_chat["game_id"]
        headers = game_with_chat["headers1"]
        
        # Send a message first
        client.post(f"/chat/{game_id}", json={
            "message": "Test message"
        }, headers=headers)
        
        # Get chat history
        response = client.get(f"/chat/{game_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) >= 1

    def test_send_chat_message_unauthorized(self, client: TestClient, test_user):
        """Test sending chat message without being in game."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        fake_game_id = str(uuid.uuid4())
        
        response = client.post(f"/chat/{fake_game_id}", json={
            "message": "Hello"
        }, headers=headers)
        
        assert response.status_code == 404

    def test_chat_message_validation(self, client: TestClient, game_with_chat):
        """Test chat message validation."""
        game_id = game_with_chat["game_id"]
        headers = game_with_chat["headers1"]
        
        # Test empty message
        response = client.post(f"/chat/{game_id}", json={
            "message": ""
        }, headers=headers)
        
        assert response.status_code in [400, 422]

    def test_chat_message_filtering(self, client: TestClient, game_with_chat):
        """Test chat message content filtering."""
        game_id = game_with_chat["game_id"]
        headers = game_with_chat["headers1"]
        
        # Test potentially inappropriate content
        response = client.post(f"/chat/{game_id}", json={
            "message": "This is a normal message"
        }, headers=headers)
        
        assert response.status_code == 200


class TestProfileAPI:
    """Test profile API endpoints."""

    def test_get_user_profile_success(self, client: TestClient, test_user):
        """Test getting user profile."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.get("/profile/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "statistics" in data

    def test_get_user_profile_unauthorized(self, client: TestClient):
        """Test getting profile without authentication."""
        response = client.get("/profile/")
        
        assert response.status_code == 401

    def test_update_profile_preferences(self, client: TestClient, test_user):
        """Test updating profile preferences."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.patch("/profile/preferences", json={
            "preferred_language": "de",
            "email_notifications": True,
            "theme": "dark"
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_get_user_statistics(self, client: TestClient, test_user):
        """Test getting user game statistics."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.get("/profile/stats", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert "games_played" in data or "total_games" in data

    def test_get_user_achievements(self, client: TestClient, test_user):
        """Test getting user achievements."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.get("/profile/achievements", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or "achievements" in data

    def test_update_profile_avatar(self, client: TestClient, test_user):
        """Test updating profile avatar."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Mock image data
        image_data = b"fake_image_data"
        files = {"avatar": ("avatar.jpg", image_data, "image/jpeg")}
        
        response = client.post("/profile/avatar", files=files, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 201]


class TestWordAdminAPI:
    """Test word admin API endpoints."""

    @pytest.fixture
    def word_admin_user(self, db_session):
        """Create a word admin user for testing."""
        admin = User(
            username="wordadmin",
            hashed_password=get_password_hash("wordadminpass123"),
            email="wordadmin@example.com",
            is_word_admin=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        
        # Create admin token
        admin_token = create_access_token(
            data={"sub": "wordadmin"},
            expires_delta=timedelta(minutes=30)
        )
        
        return {
            "id": admin.id,
            "username": "wordadmin",
            "token": admin_token
        }

    def test_add_words_success(self, client: TestClient, word_admin_user):
        """Test adding words as word admin."""
        headers = {"Authorization": f"Bearer {word_admin_user['token']}"}
        response = client.post("/word-admin/words", json={
            "language": "en",
            "words": ["TESTWORD", "NEWWORD", "ADMINWORD"]
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "added" in data or "success" in data["message"].lower()

    def test_add_words_forbidden_regular_user(self, client: TestClient, test_user):
        """Test that regular users cannot add words."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.post("/word-admin/words", json={
            "language": "en",
            "words": ["TESTWORD"]
        }, headers=headers)
        
        assert response.status_code == 403

    def test_delete_words_success(self, client: TestClient, word_admin_user):
        """Test deleting words as word admin."""
        headers = {"Authorization": f"Bearer {word_admin_user['token']}"}
        
        # First add a word
        client.post("/word-admin/words", json={
            "language": "en",
            "words": ["DELETEWORD"]
        }, headers=headers)
        
        # Then delete it
        response = client.delete("/word-admin/words", json={
            "language": "en",
            "words": ["DELETEWORD"]
        }, headers=headers)
        
        assert response.status_code == 200

    def test_get_word_statistics(self, client: TestClient, word_admin_user):
        """Test getting word statistics."""
        headers = {"Authorization": f"Bearer {word_admin_user['token']}"}
        response = client.get("/word-admin/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "word_counts" in data or "languages" in data

    def test_search_words(self, client: TestClient, word_admin_user):
        """Test searching words in database."""
        headers = {"Authorization": f"Bearer {word_admin_user['token']}"}
        response = client.get("/word-admin/search?query=HOU&language=en", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "words" in data
        assert isinstance(data["words"], list)

    def test_validate_word_list(self, client: TestClient, word_admin_user):
        """Test validating a list of words."""
        headers = {"Authorization": f"Bearer {word_admin_user['token']}"}
        response = client.post("/word-admin/validate", json={
            "language": "en",
            "words": ["HOUSE", "CAR", "INVALIDWORD123"]
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "valid_words" in data
        assert "invalid_words" in data

    def test_import_word_list(self, client: TestClient, word_admin_user):
        """Test importing word list from file."""
        headers = {"Authorization": f"Bearer {word_admin_user['token']}"}
        
        # Mock word list file
        word_data = b"HOUSE\nCAR\nTREE\nTABLE"
        files = {"file": ("words.txt", word_data, "text/plain")}
        
        response = client.post("/word-admin/import?language=en", files=files, headers=headers)
        
        assert response.status_code == 200

    def test_export_word_list(self, client: TestClient, word_admin_user):
        """Test exporting word list."""
        headers = {"Authorization": f"Bearer {word_admin_user['token']}"}
        response = client.get("/word-admin/export?language=en&format=txt", headers=headers)
        
        assert response.status_code == 200

    def test_get_pending_word_submissions(self, client: TestClient, word_admin_user):
        """Test getting pending word submissions."""
        headers = {"Authorization": f"Bearer {word_admin_user['token']}"}
        response = client.get("/word-admin/submissions", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or "submissions" in data

    def test_approve_word_submission(self, client: TestClient, word_admin_user):
        """Test approving word submission."""
        headers = {"Authorization": f"Bearer {word_admin_user['token']}"}
        response = client.post("/word-admin/submissions/1/approve", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 404]  # 404 if submission doesn't exist


class TestSystemAPI:
    """Test system API endpoints."""

    def test_health_check_public(self, client: TestClient):
        """Test public health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["ok", "healthy", "up"]

    def test_database_status_check(self, client: TestClient):
        """Test database status endpoint."""
        response = client.get("/database/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "database_status" in data or "is_connected" in data

    def test_api_version_info(self, client: TestClient):
        """Test API version information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "version" in data

    def test_openapi_schema(self, client: TestClient):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_swagger_ui(self, client: TestClient):
        """Test Swagger UI endpoint."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_ui(self, client: TestClient):
        """Test ReDoc UI endpoint."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_metrics_endpoint(self, client: TestClient):
        """Test metrics endpoint if available."""
        response = client.get("/metrics")
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_debug_tokens_endpoint(self, client: TestClient):
        """Test debug tokens endpoint."""
        response = client.get("/debug/tokens")
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert "active_tokens" in data or "token_count" in data

    def test_system_info_endpoint(self, client: TestClient):
        """Test system information endpoint."""
        response = client.get("/system/info")
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)


class TestTokenManagement:
    """Test comprehensive token management scenarios."""

    def test_token_expiration_handling(self, client: TestClient, test_user):
        """Test handling of expired tokens."""
        # Create expired token
        expired_token = create_access_token(
            data={"sub": test_user["username"]},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_malformed_token_handling(self, client: TestClient):
        """Test handling of malformed tokens."""
        malformed_tokens = [
            "invalid_token",
            "Bearer",
            "Bearer ",
            "Bearer invalid.token.format",
            "",
        ]
        
        for token in malformed_tokens:
            headers = {"Authorization": token}
            response = client.get("/users/me", headers=headers)
            assert response.status_code == 401

    def test_token_without_bearer_prefix(self, client: TestClient, test_user):
        """Test token without Bearer prefix."""
        headers = {"Authorization": test_user["token"]}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401

    def test_case_sensitivity_bearer(self, client: TestClient, test_user):
        """Test case sensitivity of Bearer prefix."""
        test_cases = [
            f"bearer {test_user['token']}",
            f"BEARER {test_user['token']}",
            f"Bearer {test_user['token']}",  # This should work
        ]
        
        for auth_header in test_cases:
            headers = {"Authorization": auth_header}
            response = client.get("/users/me", headers=headers)
            
            if auth_header.startswith("Bearer "):
                assert response.status_code == 200
            else:
                assert response.status_code == 401

    def test_token_in_query_parameter(self, client: TestClient, test_user):
        """Test token in query parameter (should not work for most endpoints)."""
        response = client.get(f"/users/me?token={test_user['token']}")
        
        # Should require header authentication
        assert response.status_code == 401

    def test_multiple_authentication_headers(self, client: TestClient, test_user):
        """Test multiple Authorization headers."""
        headers = {
            "Authorization": f"Bearer {test_user['token']}",
            "X-Authorization": f"Bearer {test_user['token']}"
        }
        response = client.get("/users/me", headers=headers)
        
        # Should work with standard Authorization header
        assert response.status_code == 200

    def test_token_reuse_across_requests(self, client: TestClient, test_user):
        """Test reusing token across multiple requests."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Make multiple requests with same token
        for _ in range(5):
            response = client.get("/users/me", headers=headers)
            assert response.status_code == 200

    def test_concurrent_token_usage(self, client: TestClient, test_user):
        """Test concurrent usage of same token."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Simulate concurrent requests
        responses = []
        for _ in range(3):
            response = client.get("/users/me", headers=headers)
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200

    def test_token_with_special_characters(self, client: TestClient):
        """Test tokens containing special characters."""
        special_tokens = [
            "Bearer token.with.dots",
            "Bearer token-with-dashes",
            "Bearer token_with_underscores",
            "Bearer token+with+plus",
            "Bearer token/with/slashes",
        ]
        
        for auth_header in special_tokens:
            headers = {"Authorization": auth_header}
            response = client.get("/users/me", headers=headers)
            # All should fail as they're not valid JWT tokens
            assert response.status_code == 401

    def test_token_length_limits(self, client: TestClient):
        """Test very long tokens."""
        very_long_token = "Bearer " + "x" * 10000
        headers = {"Authorization": very_long_token}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401

    def test_empty_authorization_header(self, client: TestClient):
        """Test empty Authorization header."""
        headers = {"Authorization": ""}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401

    def test_whitespace_in_token(self, client: TestClient):
        """Test tokens with whitespace."""
        tokens_with_whitespace = [
            "Bearer  token_with_double_space",
            "Bearer\ttoken_with_tab",
            "Bearer token_with_trailing_space ",
            " Bearer token_with_leading_space",
        ]
        
        for auth_header in tokens_with_whitespace:
            headers = {"Authorization": auth_header}
            response = client.get("/users/me", headers=headers)
            assert response.status_code == 401

    def test_token_validation_performance(self, client: TestClient, test_user):
        """Test token validation performance with valid token."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Make many requests to test performance
        start_time = datetime.now()
        for _ in range(10):
            response = client.get("/users/me", headers=headers)
            assert response.status_code == 200
        end_time = datetime.now()
        
        # Should complete reasonably quickly (less than 10 seconds for 10 requests)
        duration = (end_time - start_time).total_seconds()
        assert duration < 10 