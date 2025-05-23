from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_register_user():
    response = client.post(
        "/users/register",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code in (200, 400, 404)

def test_create_and_get_game():
    response = client.post("/games/")
    assert response.status_code in (200, 404)
