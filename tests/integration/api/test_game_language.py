import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from tests.test_utils import create_test_user
from datetime import datetime, timedelta
from app.auth import create_access_token

client = TestClient(app)

def get_test_token(username: str) -> str:
    return create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=30)
    )

def test_game_language_setting():
    """Test setting and getting game language."""
    username = f"lang_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    # Register and get token
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create game with default settings
    game_response = client.post(
        "/games/",
        headers=headers,
        json={"language": "en", "max_players": 2}
    )
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]
    
    # Creator is automatically added as a player, so no need to join
    
    # Get game to verify language setting
    response = client.get(f"/games/{game_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["language"] == "en"
