from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_get_rack_endpoints():
    """Test the rack-specific endpoints."""
    
    # Create a user
    username = f"rack_api_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a game and join
    game_id = client.post("/games/").json()["id"]
    join_response = client.post(f"/games/{game_id}/join", headers=headers)
    assert join_response.status_code == 200
    initial_rack = join_response.json()["rack"]
    
    # Test get rack for specific game
    game_rack_response = client.get(f"/rack/{game_id}", headers=headers)
    assert game_rack_response.status_code == 200
    assert game_rack_response.json()["rack"] == initial_rack
    
    # Test get all racks
    all_racks_response = client.get("/rack/", headers=headers)
    assert all_racks_response.status_code == 200
    racks = all_racks_response.json()["racks"]
    assert len(racks) > 0
    assert any(r["game_id"] == game_id for r in racks)
    
    # Test refill rack (should say rack is already full)
    refill_response = client.post(f"/rack/{game_id}/refill", headers=headers)
    assert refill_response.status_code == 200
    assert "bereits voll" in refill_response.json()["message"]
    
    # Create a second game to test multiple racks
    game_id2 = client.post("/games/").json()["id"]
    join_response2 = client.post(f"/games/{game_id2}/join", headers=headers)
    assert join_response2.status_code == 200
    
    # Test get all racks again
    all_racks_response2 = client.get("/rack/", headers=headers)
    assert all_racks_response2.status_code == 200
    racks2 = all_racks_response2.json()["racks"]
    assert len(racks2) > 1
    game_ids = [r["game_id"] for r in racks2]
    assert game_id in game_ids
    assert game_id2 in game_ids

def test_refill_rack_after_use():
    """Test refilling the rack after using some letters."""
    
    # Create a user
    username = f"refill_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    client.post("/users/register", json={"username": username, "password": password})
    token = client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a game and join
    game_id = client.post("/games/").json()["id"]
    join_response = client.post(f"/games/{game_id}/join", headers=headers)
    initial_rack = join_response.json()["rack"]
    
    # Create second player and start game
    username2 = f"refill2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": username2, "password": password})
    token2 = client.post("/auth/token", data={"username": username2, "password": password}).json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    client.post(f"/games/{game_id}/join", headers=headers2)
    client.post(f"/games/{game_id}/start", headers=headers)
    
    # Simulate using letters by exchanging some
    letters_to_exchange = initial_rack[:3]  # Exchange first 3 letters
    exchange_response = client.post(
        f"/games/{game_id}/exchange",
        params={"letters": letters_to_exchange},
        headers=headers
    )
    assert exchange_response.status_code == 200
    
    # Now test the refill endpoint
    # Note: In a real game, the rack would be updated after a move, not manually refilled
    # This is just to test the endpoint functionality
    refill_response = client.post(f"/rack/{game_id}/refill", headers=headers2)
    assert refill_response.status_code == 200
    refilled_rack = refill_response.json()["rack"]
    assert len(refilled_rack) == 7  # Should be full again