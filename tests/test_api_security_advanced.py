from fastapi.testclient import TestClient
from app.main import app
import uuid
import pytest
import jwt
import json
from datetime import datetime, timedelta
from tests.test_utils import get_test_token, create_test_user

client = TestClient(app)

def test_sql_injection_prevention():
    """Test that SQL injection attempts are prevented."""
    # Create a legitimate user first for authentication
    legitimate_username = f"legit_user_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    email = f"{legitimate_username}@example.com"
    
    register_response = create_test_user(client, legitimate_username, password, email)
    assert register_response.status_code == 200
    
    token = get_test_token(legitimate_username)
    headers = {"Authorization": f"Bearer {token}"}
    
    # SQL injection attempt in username during registration
    sql_injection_username = "admin' OR 1=1--"
    sql_injection_email = f"injection@example.com"
    
    # Try to register with SQL injection username
    register_response = client.post(
        "/users/register", 
        json={"username": sql_injection_username, "email": sql_injection_email, "password": password}
    )
    assert register_response.status_code in (200, 400, 404, 422)
    
    # Try to login with SQL injection
    login_response = client.post(
        "/auth/token", 
        data={"username": "' OR 1=1--", "password": "anything"}
    )
    # This should fail with 401 (Unauthorized) or 400 (Bad Request) or 404 (Not Found)
    assert login_response.status_code in (400, 401, 404)
    
    # Try SQL injection in game ID with proper authentication
    game_id = "' OR 1=1--"
    response = client.get(f"/games/{game_id}", headers=headers)
    assert response.status_code in (404, 422)  # Should return not found, not all games

