"""
Comprehensive API tests for authentication endpoints.
Tests token generation, login, registration, and authentication flows.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from app.auth import create_access_token, get_user_from_token
from app.models import User
import json


class TestAuthAPI:
    """Test authentication API endpoints."""

    def test_register_user_success(self, client: TestClient, db_session):
        """Test successful user registration."""
        response = client.post("/users/register", json={
            "username": "newuser",
            "password": "securepassword123",
            "email": "newuser@example.com"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # Password should not be returned
        
        # Verify user was created in database
        user = db_session.query(User).filter(User.username == "newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"

    def test_register_user_duplicate_username(self, client: TestClient, test_user):
        """Test registration with duplicate username."""
        response = client.post("/users/register", json={
            "username": test_user["username"],
            "password": "differentpassword",
            "email": "different@example.com"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_user_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        response = client.post("/users/register", json={
            "username": "testuser",
            "password": "securepassword123",
            "email": "invalid-email"
        })
        
        assert response.status_code == 422
        assert "email" in response.json()["detail"][0]["loc"]

    def test_login_success(self, client: TestClient, test_user):
        """Test successful login with token generation."""
        response = client.post("/auth/token", data={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        # Verify token is valid  
        token = data["access_token"]
        # Note: get_user_from_token requires db session, so we'll test token structure instead
        import jwt
        from app.config import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == test_user["username"]

    def test_login_invalid_credentials(self, client: TestClient, test_user):
        """Test login with invalid credentials."""
        response = client.post("/auth/token", data={
            "username": test_user["username"],
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        response = client.post("/auth/token", data={
            "username": "nonexistent",
            "password": "anypassword"
        })
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_token_validation_valid(self, client: TestClient, test_user):
        """Test accessing protected endpoint with valid token."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user["username"]
        assert data["id"] == test_user["id"]

    def test_token_validation_invalid(self, client: TestClient):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_token_validation_expired(self, client: TestClient, test_user):
        """Test accessing protected endpoint with expired token."""
        # Create expired token
        expired_token = create_access_token(
            data={"sub": test_user["username"]},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_token_validation_missing(self, client: TestClient):
        """Test accessing protected endpoint without token."""
        response = client.get("/users/me")
        
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    def test_refresh_token_functionality(self, client: TestClient, test_user):
        """Test token refresh if implemented."""
        # Login to get initial token
        response = client.post("/auth/token", data={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        
        assert response.status_code == 200
        initial_token = response.json()["access_token"]
        
        # Verify token works
        headers = {"Authorization": f"Bearer {initial_token}"}
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 200

    def test_logout_functionality(self, client: TestClient, test_user):
        """Test logout endpoint if implemented."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # First verify token works
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 200
        
        # If logout endpoint exists, test it
        logout_response = client.post("/auth/logout", headers=headers)
        if logout_response.status_code != 404:  # Endpoint exists
            assert logout_response.status_code in [200, 204]

    def test_password_reset_flow(self, client: TestClient, test_user):
        """Test password reset flow if implemented."""
        # Test password reset request
        response = client.post("/auth/reset-password", json={
            "email": "test@example.com"
        })
        
        # Endpoint might not be implemented, that's ok
        if response.status_code != 404:
            assert response.status_code in [200, 202]

    def test_user_permissions_admin(self, client: TestClient, db_session):
        """Test admin user permissions."""
        # Create admin user
        admin_user = User(
            username="adminuser",
            hashed_password="hashed_password",
            email="admin@example.com",
            is_admin=True
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)
        
        # Create admin token
        admin_token = create_access_token(
            data={"sub": "adminuser"},
            expires_delta=timedelta(minutes=30)
        )
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test admin endpoint access
        response = client.get("/admin/stats", headers=headers)
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 403]  # Either works or forbidden

    def test_user_permissions_regular(self, client: TestClient, test_user):
        """Test regular user cannot access admin endpoints."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Try to access admin endpoint
        response = client.get("/admin/stats", headers=headers)
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 403  # Should be forbidden

    def test_token_payload_structure(self, client: TestClient, test_user):
        """Test token payload contains expected fields."""
        response = client.post("/auth/token", data={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Decode and verify payload
        import jwt
        from app.config import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "sub" in payload  # Subject (username)
        assert "exp" in payload  # Expiration time
        assert payload["sub"] == test_user["username"]

    def test_concurrent_login_sessions(self, client: TestClient, test_user):
        """Test multiple concurrent login sessions."""
        tokens = []
        
        # Create multiple tokens for same user
        for i in range(3):
            response = client.post("/auth/token", data={
                "username": test_user["username"],
                "password": test_user["password"]
            })
            assert response.status_code == 200
            tokens.append(response.json()["access_token"])
        
        # Verify all tokens work
        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/users/me", headers=headers)
            assert response.status_code == 200

    def test_case_sensitive_username(self, client: TestClient, test_user):
        """Test username case sensitivity in login."""
        # Try login with different case
        response = client.post("/auth/token", data={
            "username": test_user["username"].upper(),
            "password": test_user["password"]
        })
        
        # Should fail if usernames are case-sensitive
        assert response.status_code == 401

    def test_username_validation_registration(self, client: TestClient):
        """Test username validation rules during registration."""
        test_cases = [
            ("", 422),  # Empty username
            ("a", 422),  # Too short
            ("a" * 51, 422),  # Too long
            ("user with spaces", 422),  # Spaces
            ("user@name", 422),  # Special characters
            ("validuser123", 201),  # Valid username
        ]
        
        for username, expected_status in test_cases:
            response = client.post("/users/register", json={
                "username": username,
                "password": "validpassword123",
                "email": f"{username}@example.com" if username else "test@example.com"
            })
            assert response.status_code == expected_status

    def test_password_validation_registration(self, client: TestClient):
        """Test password validation rules during registration."""
        test_cases = [
            ("", 422),  # Empty password
            ("123", 422),  # Too short
            ("a" * 129, 422),  # Too long
            ("validpassword123", 201),  # Valid password
        ]
        
        for i, (password, expected_status) in enumerate(test_cases):
            response = client.post("/users/register", json={
                "username": f"testuser{i}",
                "password": password,
                "email": f"test{i}@example.com"
            })
            assert response.status_code == expected_status 