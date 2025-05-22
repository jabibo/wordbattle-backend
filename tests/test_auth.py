from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_login_token():
    username = f"authuser_{uuid.uuid4().hex[:6]}"
    password = "secret"

    # Registrierung über API
    register = client.post("/users/register", json={"username": username, "password": password})
    assert register.status_code in (200, 400)

    # Login-Versuch
    response = client.post("/auth/token", data={"username": username, "password": password})
    print("Login status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 200
    assert "access_token" in response.json()
