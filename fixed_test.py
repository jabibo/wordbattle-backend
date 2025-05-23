from fastapi.testclient import TestClient
from app.main import app
import uuid
import pytest
import jwt
import json
from datetime import datetime, timedelta

client = TestClient(app)

def test_sql_injection_prevention():
    """Test that SQL injection attempts are prevented."""
    # SQL injection attempt in username
    sql_injection_username = "admin' OR 1=1--"
    password = "testpass"
    
    # Try to register with SQL injection username
    register_response = client.post(
        "/users/register", 
        json={"username": sql_injection_username, "password": password}
    )
    assert register_response.status_code in (200, 400)  # Either accept or reject SQL in username
    
    # Try to login with SQL injection
    login_response = client.post(
        "/auth/token", 
        data={"username": "' OR 1=1--", "password": "anything"}
    )
    # This should fail with 401 (Unauthorized) or 400 (Bad Request)
    assert login_response.status_code in (400, 401)
    
    # Try SQL injection in game ID
    game_id = "' OR 1=1--"
    response = client.get(f"/games/{game_id}")
    assert response.status_code == 404  # Should return not found, not all games
