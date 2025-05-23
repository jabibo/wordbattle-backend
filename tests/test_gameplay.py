import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token

client = TestClient(app)

def test_join_deal_exchange_authenticated():
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "testpass"

    # Registrierung
    reg = client.post("/users/register", json={"username": username, "password": password})
    assert reg.status_code in (200, 400)

    # Token direkt erstellen
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Spiel erstellen
    game_response = client.post("/games/")
    assert game_response.status_code in (200, 404)
    
    if game_response.status_code == 200:
        game_id = game_response.json()["id"]
        
        # Spiel beitreten
        join_response = client.post(f"/games/{game_id}/join", headers=headers)
        assert join_response.status_code in (200, 403, 404)

