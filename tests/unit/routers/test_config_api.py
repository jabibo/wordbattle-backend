"""
Comprehensive tests for config API endpoint.
Tests configuration retrieval and validation.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestConfigAPI:
    """Test suite for configuration API."""
    
    def test_get_config_success(self):
        """Test getting API configuration successfully."""
        response = client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "config" in data
    
    def test_config_has_api_version(self):
        """Test that config includes API version."""
        response = client.get("/config")
        config = response.json()["config"]
        
        assert "api_version" in config
        assert isinstance(config["api_version"], str)
    
    def test_config_has_environment(self):
        """Test that config includes environment."""
        response = client.get("/config")
        config = response.json()["config"]
        
        assert "environment" in config
        assert isinstance(config["environment"], str)
    
    def test_config_has_features(self):
        """Test that config includes features."""
        response = client.get("/config")
        config = response.json()["config"]
        
        assert "features" in config
        features = config["features"]
        assert isinstance(features, dict)
        
        # Check key features
        assert "email_verification" in features
        assert "persistent_login" in features
        assert "game_invitations" in features
        assert "computer_players" in features
        assert "word_challenges" in features
    
    def test_config_has_game_settings(self):
        """Test that config includes game settings."""
        response = client.get("/config")
        config = response.json()["config"]
        
        assert "game" in config
        game = config["game"]
        
        assert "supported_languages" in game
        assert isinstance(game["supported_languages"], list)
        assert len(game["supported_languages"]) > 0
        
        assert "max_players" in game
        assert isinstance(game["max_players"], int)
        assert game["max_players"] > 0
        
        assert "min_players" in game
        assert isinstance(game["min_players"], int)
        assert game["min_players"] > 0
    
    def test_config_supported_languages(self):
        """Test that supported languages are configured."""
        response = client.get("/config")
        config = response.json()["config"]
        languages = config["game"]["supported_languages"]
        
        # Check common languages
        assert "en" in languages  # English
        assert "de" in languages  # German
        assert len(languages) >= 2
    
    def test_config_player_limits(self):
        """Test that player limits are reasonable."""
        response = client.get("/config")
        config = response.json()["config"]
        game = config["game"]
        
        assert game["min_players"] <= game["max_players"]
        assert game["min_players"] >= 2  # At least 2 players needed
        assert game["max_players"] <= 10  # Reasonable upper bound
    
    def test_config_has_auth_settings(self):
        """Test that config includes auth settings."""
        response = client.get("/config")
        config = response.json()["config"]
        
        assert "auth" in config
        auth = config["auth"]
        
        assert "verification_code_length" in auth
        assert isinstance(auth["verification_code_length"], int)
        
        assert "verification_code_expires_minutes" in auth
        assert isinstance(auth["verification_code_expires_minutes"], int)
        
        assert "access_token_expires_minutes" in auth
        assert isinstance(auth["access_token_expires_minutes"], int)
        
        assert "persistent_token_expires_days" in auth
        assert isinstance(auth["persistent_token_expires_days"], int)
    
    def test_config_has_limits(self):
        """Test that config includes rate limits."""
        response = client.get("/config")
        config = response.json()["config"]
        
        assert "limits" in config
        limits = config["limits"]
        
        assert "max_games_per_user" in limits
        assert isinstance(limits["max_games_per_user"], int)
        assert limits["max_games_per_user"] > 0
        
        assert "rate_limit_requests_per_minute" in limits
        assert isinstance(limits["rate_limit_requests_per_minute"], int)
    
    def test_config_has_ui_settings(self):
        """Test that config includes UI settings."""
        response = client.get("/config")
        config = response.json()["config"]
        
        assert "ui" in config
        ui = config["ui"]
        
        assert "default_language" in ui
        assert isinstance(ui["default_language"], str)
        
        assert "available_themes" in ui
        assert isinstance(ui["available_themes"], list)
        
        assert "default_theme" in ui
        assert isinstance(ui["default_theme"], str)
    
    def test_config_difficulties_valid(self):
        """Test that game difficulties are configured."""
        response = client.get("/config")
        config = response.json()["config"]
        game = config["game"]
        
        assert "difficulties" in game
        difficulties = game["difficulties"]
        assert isinstance(difficulties, list)
        assert len(difficulties) > 0
        
        # Check common difficulties
        assert "easy" in [d.lower() for d in difficulties]
        assert "normal" in [d.lower() for d in difficulties] or "medium" in [d.lower() for d in difficulties]
    
    def test_config_computer_difficulties(self):
        """Test that computer player difficulties are configured."""
        response = client.get("/config")
        config = response.json()["config"]
        game = config["game"]
        
        assert "computer_difficulties" in game
        assert isinstance(game["computer_difficulties"], list)
        assert len(game["computer_difficulties"]) > 0
    
    def test_config_default_time_limit(self):
        """Test that default time limit is configured."""
        response = client.get("/config")
        config = response.json()["config"]
        game = config["game"]
        
        assert "default_time_limit" in game
        assert isinstance(game["default_time_limit"], int)
        assert game["default_time_limit"] >= 0
    
    def test_config_json_serializable(self):
        """Test that config is JSON serializable."""
        response = client.get("/config")
        
        # Should not raise exception
        data = response.json()
        assert data is not None
    
    def test_config_response_format(self):
        """Test that response follows standard format."""
        response = client.get("/config")
        data = response.json()
        
        assert "success" in data
        assert isinstance(data["success"], bool)
        assert "config" in data
        assert isinstance(data["config"], dict)
    
    def test_config_themes_contain_default(self):
        """Test that available themes include the default theme."""
        response = client.get("/config")
        config = response.json()["config"]
        ui = config["ui"]
        
        assert ui["default_theme"] in ui["available_themes"]
    
    def test_config_default_language_in_supported(self):
        """Test that default language is in supported languages."""
        response = client.get("/config")
        config = response.json()["config"]
        
        default_lang = config["ui"]["default_language"]
        supported_langs = config["game"]["supported_languages"]
        
        assert default_lang in supported_langs
    
    def test_config_consistent_across_calls(self):
        """Test that config is consistent across multiple calls."""
        response1 = client.get("/config")
        response2 = client.get("/config")
        
        assert response1.json() == response2.json()


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_all_feature_flags_are_boolean(self):
        """Test that all feature flags are boolean values."""
        response = client.get("/config")
        features = response.json()["config"]["features"]
        
        for feature_name, feature_value in features.items():
            assert isinstance(feature_value, bool), f"Feature {feature_name} should be boolean"
    
    def test_all_limits_are_positive(self):
        """Test that all limits are positive integers."""
        response = client.get("/config")
        limits = response.json()["config"]["limits"]
        
        for limit_name, limit_value in limits.items():
            assert isinstance(limit_value, int), f"Limit {limit_name} should be integer"
            assert limit_value > 0, f"Limit {limit_name} should be positive"
    
    def test_all_timeouts_are_positive(self):
        """Test that all timeout values are positive."""
        response = client.get("/config")
        auth = response.json()["config"]["auth"]
        
        for key, value in auth.items():
            if "expires" in key or "minutes" in key or "days" in key:
                assert isinstance(value, int)
                assert value > 0
    
    def test_verification_code_length_reasonable(self):
        """Test that verification code length is reasonable."""
        response = client.get("/config")
        auth = response.json()["config"]["auth"]
        
        code_length = auth["verification_code_length"]
        assert 4 <= code_length <= 10  # Reasonable range


class TestConfigEndpointBehavior:
    """Test endpoint behavior and error handling."""
    
    def test_config_endpoint_method_get(self):
        """Test that GET method is supported."""
        response = client.get("/config")
        assert response.status_code == 200
    
    def test_config_endpoint_method_post_not_allowed(self):
        """Test that POST method is not allowed."""
        response = client.post("/config", json={})
        assert response.status_code == 405  # Method not allowed
    
    def test_config_endpoint_no_authentication_required(self):
        """Test that config endpoint doesn't require authentication."""
        # Should work without any auth headers
        response = client.get("/config")
        assert response.status_code == 200
    
    def test_config_response_headers(self):
        """Test response headers."""
        response = client.get("/config")
        
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

