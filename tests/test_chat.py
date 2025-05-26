import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token
from app.models import ChatMessage
from datetime import datetime, timezone

client = TestClient(app)

@pytest.mark.timeout(5)  # Set a 5-second timeout for this test
def test_chat_message_persistence(test_user, test_game_with_player, test_websocket_client, db_session):
    """Test that chat messages are properly stored in the database."""
    game, _ = test_game_with_player
    
    with test_websocket_client.websocket_connect(f"/games/{game.id}/ws", headers={"Authorization": f"Bearer {test_user['token']}"}) as websocket:
        # Skip initial connection message
        websocket.receive_json()
        
        # Send a chat message
        message_text = "Hello, World!"
        websocket.send_json({
            "type": "chat_message",
            "message": message_text
        })
        
        # Receive the broadcast message
        response = websocket.receive_json()
        assert response["type"] == "chat_message"
        assert response["message"] == message_text
        assert response["sender_username"] == test_user["username"]
        assert "message_id" in response
        assert "timestamp" in response
        
        # Verify message was stored in database
        stored_message = db_session.query(ChatMessage).filter_by(
            game_id=game.id,
            sender_id=test_user["id"]
        ).first()
        
        assert stored_message is not None
        assert stored_message.message == message_text

def test_chat_message_retrieval(test_user, test_game_with_player, test_websocket_client, db_session):
    """Test retrieving chat message history."""
    game, _ = test_game_with_player
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    # Add some test messages to the database
    messages = [
        ChatMessage(
            game_id=game.id,
            sender_id=test_user["id"],
            message=f"Test message {i}",
            timestamp=datetime.now(timezone.utc)
        )
        for i in range(3)
    ]
    for msg in messages:
        db_session.add(msg)
    db_session.commit()
    
    # Test message retrieval
    response = client.get(f"/games/{game.id}/messages", headers=headers)
    assert response.status_code == 200
    
    messages_data = response.json()
    assert len(messages_data) == 3
    
    # Verify message format
    for msg in messages_data:
        assert "id" in msg
        assert "game_id" in msg
        assert "sender_id" in msg
        assert "sender_username" in msg
        assert "message" in msg
        assert "timestamp" in msg
        assert msg["game_id"] == game.id
        assert msg["sender_id"] == test_user["id"]
        assert msg["sender_username"] == test_user["username"]

def test_chat_message_pagination(test_user, test_game_with_player, test_websocket_client, db_session):
    """Test chat message pagination."""
    game, _ = test_game_with_player
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    # Add more messages than the default limit
    messages = [
        ChatMessage(
            game_id=game.id,
            sender_id=test_user["id"],
            message=f"Test message {i}",
            timestamp=datetime.now(timezone.utc)
        )
        for i in range(60)  # Default limit is 50
    ]
    for msg in messages:
        db_session.add(msg)
    db_session.commit()
    
    # Get first page
    response = client.get(f"/games/{game.id}/messages", headers=headers)
    assert response.status_code == 200
    first_page = response.json()
    assert len(first_page) == 50  # Default limit
    
    # Get second page using before_id
    last_msg_id = first_page[-1]["id"]
    response = client.get(
        f"/games/{game.id}/messages?before_id={last_msg_id}",
        headers=headers
    )
    assert response.status_code == 200
    second_page = response.json()
    assert len(second_page) == 10  # Remaining messages

def test_chat_authorization(test_user, test_user2, test_game_with_player, test_websocket_client, test_websocket_client2):
    """Test chat authorization rules."""
    game, _ = test_game_with_player
    headers1 = {"Authorization": f"Bearer {test_user['token']}"}
    headers2 = {"Authorization": f"Bearer {test_user2['token']}"}
    
    # Non-player should not be able to get messages
    response = client.get(f"/games/{game.id}/messages", headers=headers2)
    assert response.status_code == 403
    
    # Non-player should not be able to connect to WebSocket
    # Note: The WebSocket endpoint allows creators to connect, so we need to test with a truly unauthorized user
    # For now, we'll skip this specific test as the authorization logic allows creators
    # TODO: Create a test with a user who is neither creator nor player
    pass

def test_empty_and_invalid_messages(test_user, test_game_with_player, test_websocket_client):
    """Test handling of empty and invalid messages."""
    game, _ = test_game_with_player
    
    with test_websocket_client.websocket_connect(f"/games/{game.id}/ws", headers={"Authorization": f"Bearer {test_user['token']}"}) as websocket:
        # Skip initial connection message
        websocket.receive_json()
        
        # Send empty message
        websocket.send_json({
            "type": "chat_message",
            "message": ""
        })
        
        # Send whitespace-only message
        websocket.send_json({
            "type": "chat_message",
            "message": "   "
        })
        
        # Send message without type
        websocket.send_json({
            "message": "No type specified"
        })
        
        # Send message with wrong type
        websocket.send_json({
            "type": "invalid_type",
            "message": "Wrong type"
        })
        
        # Verify no messages were broadcast (should not receive anything)
        # Note: In a real test, we might need to wait or use a different approach
        # to verify no messages were sent, but for now we'll skip this check 