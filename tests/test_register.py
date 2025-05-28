import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from tests.test_utils import create_test_user

client = TestClient(app)

def test_register_user():
    """Test user registration with email."""
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"
    password = "testpassword"
    
    user_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["username"] == username
    assert data["email"] == email
    assert "id" in data
    assert "password" not in data  # Password should not be returned

def test_register_user_email_only():
    """Test user registration with email-only authentication."""
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"
    
    user_data = {
        "username": username,
        "email": email
    }
    
    response = client.post("/users/register-email-only", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["username"] == username
    assert data["email"] == email
    assert data["auth_method"] == "email_only"
    assert "id" in data

def test_register_duplicate_username():
    """Test that duplicate usernames are rejected."""
    username = f"duplicate_{uuid.uuid4().hex[:6]}"
    email1 = f"{username}1@example.com"
    email2 = f"{username}2@example.com"
    password = "testpassword"
    
    # Register first user
    user_data1 = {
        "username": username,
        "email": email1,
        "password": password
    }
    response1 = client.post("/users/register", json=user_data1)
    assert response1.status_code == 200
    
    # Try to register second user with same username
    user_data2 = {
        "username": username,
        "email": email2,
        "password": password
    }
    response2 = client.post("/users/register", json=user_data2)
    assert response2.status_code == 400
    assert "Username already taken" in response2.json()["detail"]

def test_register_duplicate_email():
    """Test that duplicate emails are rejected."""
    username1 = f"user1_{uuid.uuid4().hex[:6]}"
    username2 = f"user2_{uuid.uuid4().hex[:6]}"
    email = f"shared@example.com"
    password = "testpassword"
    
    # Register first user
    user_data1 = {
        "username": username1,
        "email": email,
        "password": password
    }
    response1 = client.post("/users/register", json=user_data1)
    assert response1.status_code == 200
    
    # Try to register second user with same email
    user_data2 = {
        "username": username2,
        "email": email,
        "password": password
    }
    response2 = client.post("/users/register", json=user_data2)
    assert response2.status_code == 400
    assert "Email already registered" in response2.json()["detail"] 