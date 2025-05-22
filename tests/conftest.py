import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import User, Game, Player, Move
from app.auth import get_password_hash

@pytest.fixture(scope="function")
def test_db():
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(test_db):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.dependencies import get_db
    
    # Override the get_db dependency to use the test database
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Remove the override after the test
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(test_db):
    # Create a test user
    user = User(
        username="testuser",
        hashed_password=get_password_hash("testpassword")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user