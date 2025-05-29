import pytest
from fastapi.testclient import TestClient
import json
from tests.conftest import client, test_user, test_game_with_player

def test_websocket_connection(client, test_user, test_game_with_player):
    """Test WebSocket connection to a game."""
    game, _ = test_game_with_player
    
    with client.websocket_connect(f"/ws/games/{game.id}?token={test_user['token']}") as websocket:
        # Receive initial connection confirmation
        response = websocket.receive_json()
        assert "type" in response
        assert response["type"] == "connection_established"
        assert "game_state" in response
        
        # For now, just test the connection - chat functionality would need to be implemented
        # in the WebSocket endpoint to handle incoming messages
        assert True  # Connection successful 