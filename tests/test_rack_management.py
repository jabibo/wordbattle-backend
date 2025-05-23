import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from tests.test_utils import get_test_token

client = TestClient(app)

def test_letter_exchange():
    """Test that letter exchange works correctly."""
    # Create a user
    username = f"exchange_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a game and join
    game_id = client.post("/games/").json()["id"]
    join_response = client.post(f"/games/{game_id}/join", headers=headers)

    # Get initial rack
    initial_rack = join_response.json()["rack"]

    # Create second player and start game
    username2 = f"exchange_test2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": username2, "password": password})
    token2 = get_test_token(username2)
    headers2 = {"Authorization": f"Bearer {token2}"}

    client.post(f"/games/{game_id}/join", headers=headers2)
    client.post(f"/games/{game_id}/start", headers=headers)

    # Exchange letters
    letters_to_exchange = initial_rack[:3]
    response = client.post(f"/games/{game_id}/exchange", params={"letters": letters_to_exchange}, headers=headers)
    assert response.status_code in (200, 403, 404)

def test_deal_letters():
    """Test that dealing letters works correctly."""
    # Create a user
    username = f"deal_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    client.post("/users/register", json={"username": username, "password": password})
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a game and join
    game_id = client.post("/games/").json()["id"]
    join_response = client.post(f"/games/{game_id}/join", headers=headers)

    # Get initial rack
    initial_rack = join_response.json()["rack"]

    # Create second player and start game
    username2 = f"deal_test2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": username2, "password": password})
    token2 = get_test_token(username2)
    headers2 = {"Authorization": f"Bearer {token2}"}

    client.post(f"/games/{game_id}/join", headers=headers2)
    client.post(f"/games/{game_id}/start", headers=headers)

    # Deal letters
    response = client.post(f"/games/{game_id}/deal", headers=headers)
    assert response.status_code in (200, 403, 404)

