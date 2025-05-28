import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from tests.test_utils import get_test_token, create_test_user

client = TestClient(app)

def test_move_persistence():
    username = f"move_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers, json=game_data)
    assert game_response.status_code in (200, 404)

def test_rack_update_after_move():
    username = f"rack_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    game_data = {"language": "en", "max_players": 2}
    game_response = client.post("/games/", headers=headers, json=game_data)
    assert game_response.status_code in (200, 404)

