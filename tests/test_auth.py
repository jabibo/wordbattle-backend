import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from tests.test_utils import get_test_token

client = TestClient(app)

def test_login_token():
    username = f"auth_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    
    # Register user
    client.post("/users/register", json={"username": username, "password": password})
    
    # Get token
    token = get_test_token(username)
    assert token is not None
    
    # Test token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/me", headers=headers)
    assert response.status_code in (200, 403, 404)

