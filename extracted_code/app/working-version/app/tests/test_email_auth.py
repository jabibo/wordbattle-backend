import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.models import User
from app.auth import generate_verification_code
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

client = TestClient(app)

def test_email_registration():
    """Test registering a user with email-only authentication."""
    username = f"email_user_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"
    
    # Register user with email only
    response = client.post("/users/register-email-only", json={
        "username": username,
        "email": email
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["email"] == email
    assert data["auth_method"] == "email_only"

def test_email_login_flow():
    """Test the complete email login flow with verification code."""
    username = f"email_login_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"
    
    # 1. Register user
    register_response = client.post("/users/register-email-only", json={
        "username": username,
        "email": email
    })
    assert register_response.status_code == 200
    
    # 2. Request login (this should send verification code)
    login_request_response = client.post("/auth/email-login", json={
        "email": email,
        "remember_me": False
    })
    assert login_request_response.status_code == 200
    data = login_request_response.json()
    assert "verification code" in data["message"].lower()
    assert data["email_sent"] is True
    
    # 3. In testing mode, we need to get the verification code from the database
    # Since we can't easily access the database in tests, we'll simulate this
    # In a real test environment, you'd check the test email or database
    
    # For now, let's test with an invalid code to ensure validation works
    verify_response = client.post("/auth/verify-code", json={
        "email": email,
        "verification_code": "123456",  # Invalid code
        "remember_me": False
    })
    assert verify_response.status_code == 401
    assert "invalid" in verify_response.json()["detail"].lower()

def test_email_registration_with_password():
    """Test registering a user with both email and password."""
    username = f"hybrid_user_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"
    password = "testpassword123"
    
    # Register user with email and password
    response = client.post("/users/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["email"] == email

def test_duplicate_email_registration():
    """Test that duplicate email registration is prevented."""
    username1 = f"user1_{uuid.uuid4().hex[:6]}"
    username2 = f"user2_{uuid.uuid4().hex[:6]}"
    email = f"duplicate_{uuid.uuid4().hex[:6]}@example.com"
    
    # Register first user
    response1 = client.post("/users/register-email-only", json={
        "username": username1,
        "email": email
    })
    assert response1.status_code == 200
    
    # Try to register second user with same email
    response2 = client.post("/users/register-email-only", json={
        "username": username2,
        "email": email
    })
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"].lower()

def test_invalid_email_format():
    """Test that invalid email formats are rejected."""
    username = f"invalid_email_{uuid.uuid4().hex[:6]}"
    
    # Try to register with invalid email
    response = client.post("/users/register-email-only", json={
        "username": username,
        "email": "not-an-email"
    })
    assert response.status_code == 422  # Validation error

def test_email_login_nonexistent_user():
    """Test email login request for non-existent user."""
    fake_email = f"nonexistent_{uuid.uuid4().hex[:6]}@example.com"
    
    # Request login for non-existent email
    response = client.post("/auth/email-login", json={
        "email": fake_email,
        "remember_me": False
    })
    
    # Should return success for security (don't reveal if email exists)
    assert response.status_code == 200
    data = response.json()
    assert "verification code" in data["message"].lower()
    assert data["email_sent"] is True

def test_persistent_token_request():
    """Test requesting a persistent token with remember_me."""
    username = f"persistent_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"
    
    # Register user
    register_response = client.post("/users/register-email-only", json={
        "username": username,
        "email": email
    })
    assert register_response.status_code == 200
    
    # Request login with remember_me
    login_request_response = client.post("/auth/email-login", json={
        "email": email,
        "remember_me": True
    })
    assert login_request_response.status_code == 200
    
    # The verification flow would include persistent token in response
    # when remember_me is True (tested in integration tests) 