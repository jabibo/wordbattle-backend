import pytest
from fastapi.testclient import TestClient
import json
from tests.conftest import client, test_user, test_game_with_player

def test_websocket_connection(client, test_user, test_game_with_player):
    """Test WebSocket connection to a game."""
    game, _ = test_game_with_player
    
    with client.websocket_connect(f"/ws/games/{game.id}?token={test_user['token']}") as websocket:
        # Receive initial game state
        response = websocket.receive_json()
        assert "type" in response
        assert response["type"] == "game_state"
        
        # Send a test message
        websocket.send_json({
            "type": "chat_message",
            "message": "Hello, World!"
        })
        
        # Receive the broadcast message
        response = websocket.receive_json()
        assert response["type"] == "chat_message"
        assert response["message"] == "Hello, World!"
        assert response["sender_username"] == test_user["username"] 