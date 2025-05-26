import pytest
from fastapi.testclient import TestClient
import uuid

def test_user_registration(client):
    """Test user registration endpoint."""
    # User data with unique username and email
    username = f"user_{uuid.uuid4().hex[:6]}"
    user_data = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpassword"
    }

    # Send POST request
    response = client.post("/users/register", json=user_data)

    # Verify response
    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data
    assert "id" in response_data
    assert "User successfully registered" in response_data["message"] 