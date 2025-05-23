import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
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
    client.post("/users/register", json={"username": username, "password": password})
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create game
    game_response = client.post("/games/")
    assert game_response.status_code == 200
    game_id = game_response.json()["id"]
    
    # Join game first
    join_response = client.post(f"/games/{game_id}/join", headers=headers)
    assert join_response.status_code == 200
    
    # Set language - should succeed with auth
    response = client.post(f"/games/{game_id}/language", headers=headers, params={"language": "en"})
    assert response.status_code == 200
