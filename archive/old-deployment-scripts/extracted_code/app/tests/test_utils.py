from datetime import datetime, timedelta
from app.auth import create_access_token
import uuid

def get_test_token(username: str) -> str:
    """Generate a test token for the given username."""
    return create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=30)
    )

def create_test_user(client, username: str = None, password: str = "testpass", email: str = None):
    """Create a test user with email and return the response."""
    if username is None:
        username = f"user_{uuid.uuid4().hex[:6]}"
    
    if email is None:
        email = f"{username}@example.com"
    
    user_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    return client.post("/users/register", json=user_data)

def create_test_user_email_only(client, username: str = None, email: str = None):
    """Create a test user with email-only authentication."""
    if username is None:
        username = f"user_{uuid.uuid4().hex[:6]}"
    
    if email is None:
        email = f"{username}@example.com"
    
    user_data = {
        "username": username,
        "email": email
    }
    
    return client.post("/users/register-email-only", json=user_data)

def create_authenticated_user(client, username: str = None, password: str = "testpass", email: str = None):
    """Create a test user and return both the response and authentication headers."""
    if username is None:
        username = f"user_{uuid.uuid4().hex[:6]}"
    
    if email is None:
        email = f"{username}@example.com"
    
    # Register user
    response = create_test_user(client, username, password, email)
    
    if response.status_code == 200:
        # Create token for authentication
        token = get_test_token(username)
        headers = {"Authorization": f"Bearer {token}"}
        return response, headers
    else:
        return response, None
