import tests.docker_test_config\nimport tests.docker_test_config\nimport tests.docker_test_config\nimport tests.docker_test_config\nimport pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import User, Game, Player, Move, WordList
from app.auth import get_password_hash, create_access_token
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

# Ensure TESTING environment variable is set
os.environ["TESTING"] = "1"

@pytest.fixture(scope='function')
def test_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope='function')
def test_user(test_db):
    username = 'testuser'
    password = 'testpassword'
    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        is_admin=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    access_token = create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=30)
    )

    return {
        'id': user.id,
        'username': username,
        'token': access_token
    }

@pytest.fixture(scope='function')
def client(test_db, test_user):
    from app.dependencies import get_db
    
    # Override the get_db dependency
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    # Override the auth dependency
    from app.auth import get_current_user
    async def override_get_current_user():
        return test_db.query(User).filter(User.username == test_user['username']).first()
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as client:
        # Add auth header to all requests
        client.headers.update({"Authorization": f"Bearer {test_user['token']}"})
        yield client
    
    app.dependency_overrides.clear()




