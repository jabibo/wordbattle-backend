import pytest
from fastapi.testclient import TestClient
import uuid

def test_user_registration(client):
    """Test user registration endpoint."""
    # User data with unique username
    user_data = {
        "username": f"user_{uuid.uuid4().hex[:6]}",
        "password": "testpassword"
    }

    # Send POST request
    response = client.post("/users/register", json=user_data)

    # Verify response
    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data
    assert "id" in response_data
    assert response_data["message"] == "Benutzer erfolgreich registriert" 