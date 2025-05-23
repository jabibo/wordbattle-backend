import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_login_invalid_credentials(test_db):
    # Create a unique username for this test
    username = f"login_test_{uuid.uuid4().hex[:6]}"
    password = "correctpass"
    wrong_password = "wrongpass"

    # Register the user with test_db directly
    from app.models import User
    from app.auth import get_password_hash
    
    user = User(
        username=username,
        hashed_password=get_password_hash(password)
    )
    test_db.add(user)
    test_db.commit()

    # Test with wrong password
    response1 = client.post(
        "/auth/token",
        data={"username": username, "password": wrong_password}
    )
    assert response1.status_code in (400, 404)  # Accept either 400 or 404

    # Test with wrong username
    response2 = client.post(
        "/auth/token",
        data={"username": "nonexistent", "password": password}
    )
    assert response2.status_code in (400, 404)  # Accept either 400 or 404
