from datetime import datetime, timedelta
from app.auth import create_access_token

def get_test_token(username: str) -> str:
    """Generate a test token for the given username."""
    return create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=30)
    )
