from fastapi.testclient import TestClient
from app.main import app
import uuid
import re

client = TestClient(app)

def test_initial_rack_distribution():
    """Test that initial rack distribution gives 7 letters."""
    
    # Create a user
    username = f"rack_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a game and join
    game_id = client.post("/games/").json()["id"]
    join_response = client.post(f"/games/{game_id}/join", headers=headers)
    
    # Check rack
    assert join_response.status_code == 200
    rack = join_response.json()["rack"]
    assert len(rack) == 7
    assert isinstance(rack, str)
    # Check that rack contains only valid letters
    assert re.match(r'^[A-ZÄÖÜ?]+$', rack)

def test_letter_exchange():
    """Test that letter exchange works correctly."""
    
    # Create a user
    username = f"exchange_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a game and join
    game_id = client.post("/games/").json()["id"]
    join_response = client.post(f"/games/{game_id}/join", headers=headers)
    
    # Get initial rack
    initial_rack = join_response.json()["rack"]
    
    # Create second player and start game
    username2 = f"exchange_test2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": username2, "password": password})
    token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    client.post(f"/games/{game_id}/join", headers=headers2)
    client.post(f"/games/{game_id}/start", headers=headers)
    
    # Exchange first letter
    letter_to_exchange = initial_rack[0]
    exchange_response = client.post(
        f"/games/{game_id}/exchange",
        params={"letters": letter_to_exchange},
        headers=headers
    )
    
    # Check exchange result
    assert exchange_response.status_code == 200
    new_rack = exchange_response.json()["new_rack"]
    assert len(new_rack) == 7  # Rack should still have 7 letters
    # The letter might still be in the rack if it was drawn again, but that's valid

def test_deal_letters():
    """Test that dealing letters works correctly."""
    
    # Create a user
    username = f"deal_test_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a game and join
    game_id = client.post("/games/").json()["id"]
    join_response = client.post(f"/games/{game_id}/join", headers=headers)
    
    # Get initial rack
    initial_rack = join_response.json()["rack"]
    
    # Create second player and start game
    username2 = f"deal_test2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": username2, "password": password})
    token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    client.post(f"/games/{game_id}/join", headers=headers2)
    client.post(f"/games/{game_id}/start", headers=headers)
    
    # Deal letters
    deal_response = client.post(f"/games/{game_id}/deal", headers=headers)
    
    # Check deal result
    assert deal_response.status_code == 200
    assert "new_rack" in deal_response.json()
    new_rack = deal_response.json()["new_rack"]
    assert len(new_rack) == 7  # Rack should have 7 letters