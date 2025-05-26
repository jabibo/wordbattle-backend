import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from app.auth import get_password_hash
from app.models import User

client = TestClient(app)

def test_login_invalid_credentials(db_session):
    # Create a test user
    username = "test_user"
    password = "test_password"
    hashed_password = get_password_hash(password)
    user = User(username=username, hashed_password=hashed_password)
    db_session.add(user)
    db_session.commit()

    # Test with wrong password
    response = client.post(
        "/auth/token",
        data={"username": username, "password": "wrong_password"}
    )
    assert response.status_code == 401

    # Test with non-existent user
    response = client.post(
        "/auth/token",
        data={"username": "nonexistent", "password": password}
    )
    assert response.status_code == 401
