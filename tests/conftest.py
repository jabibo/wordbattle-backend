import os
import pytest
import codecs
import sys
import urllib.parse
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models import User, Game, Player, Move, WordList, GameInvitation, GameStatus
from app.auth import get_password_hash, create_access_token
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.dependencies import get_db
from app.main import app
from contextlib import contextmanager
import psycopg2
from app.config import get_database_url
import json

# Set testing environment
os.environ["TESTING"] = "1"

# Force UTF-8 encoding for Windows
if sys.platform.startswith('win'):
    # Set environment variables for UTF-8 encoding
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # This is specific to Windows
    os.environ["PYTHONUTF8"] = "1"

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    # Get database URL with proper encoding
    conn_str = get_database_url(is_test=True)
    
    # Create engine with minimal connection parameters
    engine = create_engine(
        conn_str,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False,
        connect_args={
            "application_name": "wordbattle_test",
            "connect_timeout": 10,
            "client_encoding": "utf8",
            "options": "-c client_encoding=utf8 -c standard_conforming_strings=on"
        }
    )
    
    # Add event listeners to handle connection issues
    @event.listens_for(engine, "connect")
    def set_pg_settings(dbapi_connection, connection_record):
        # Set session settings for test database
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET client_encoding='UTF8';")
            cursor.execute("SET standard_conforming_strings=on;")
    
    return engine

@pytest.fixture(scope="session")
def TestingSessionLocal(engine):
    """Create a session factory for testing."""
    SessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )
    return scoped_session(SessionLocal)

@pytest.fixture(scope="session", autouse=True)
def initialize_test_database(engine):
    """Initialize test database before any tests run."""
    from app.initialize import initialize_database, create_tables
    
    # Create tables
    if not create_tables():
        pytest.fail("Failed to create database tables")
    
    # Initialize database (this will handle wordlists)
    if not initialize_database():
        pytest.fail("Failed to initialize test database")
    
    # Create a session to ensure wordlists are available
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        # Add test words for both languages
        test_words_de = ["HAUS", "AUTO", "BAUM", "TISCH", "STUHL", "ÜBER", "SCHÖN", "GRÜN"]
        test_words_en = ["HOUSE", "CAR", "TREE", "TABLE", "CHAIR", "OVER", "NICE", "GREEN"]
        
        # Clear existing wordlists
        db.query(WordList).delete()
        db.commit()
        
        # Add German words
        for word in test_words_de:
            word_bytes = word.encode('utf-8')
            word_str = word_bytes.decode('utf-8')
            db.add(WordList(language="de", word=word_str))
        
        # Add English words
        for word in test_words_en:
            db.add(WordList(language="en", word=word))
        
        db.commit()
    finally:
        db.close()
    
    yield engine

@pytest.fixture(scope="function")
def db_session(TestingSessionLocal):
    """Creates a new database session for a test."""
    session = TestingSessionLocal()
    
    try:
        # Clear all tables before each test
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        
        # Set up default test data
        test_words = ["HAUS", "AUTO", "BAUM", "TISCH", "STUHL", "ÜBER", "SCHÖN", "GRÜN"]
        for word in test_words:
            word_bytes = word.encode('utf-8')
            word_str = word_bytes.decode('utf-8')
            session.add(WordList(language="de", word=word_str))
        
        # Add English test words
        english_words = ["HOUSE", "CAR", "TREE", "TABLE", "CHAIR", "OVER", "NICE", "GREEN"]
        for word in english_words:
            session.add(WordList(language="en", word=word))
        
        # Commit test data
        session.commit()
        
        yield session
        
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
        TestingSessionLocal.remove()

@pytest.fixture(scope="function")
def client(db_session):
    """Test client with database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    test_client = TestClient(app)
    
    yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user and return user info with access token."""
    username = "testuser"
    password = "testpassword"
    
    # Check if user already exists
    existing_user = db_session.query(User).filter(User.username == username).first()
    if existing_user:
        # Delete all games created by this user
        games = db_session.query(Game).filter(Game.creator_id == existing_user.id).all()
        for game in games:
            # Delete all players and moves first
            db_session.query(Move).filter(Move.game_id == game.id).delete()
            db_session.query(Player).filter(Player.game_id == game.id).delete()
            db_session.delete(game)
        
        # Now delete the user
        db_session.delete(existing_user)
        db_session.commit()
    
    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create token with proper expiration
    access_token = create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=30)
    )

    # Set testing environment variable
    os.environ["TESTING"] = "1"

    return {
        "id": user.id,
        "username": username,
        "token": access_token,
        "password": password
    }

@pytest.fixture(scope="function")
def test_user2(db_session):
    """Create a second test user and return user info with access token."""
    username = "testuser2"
    password = "testpassword"
    
    # Check if user already exists
    existing_user = db_session.query(User).filter(User.username == username).first()
    if existing_user:
        # Delete all games created by this user
        games = db_session.query(Game).filter(Game.creator_id == existing_user.id).all()
        for game in games:
            # Delete all players and moves first
            db_session.query(Move).filter(Move.game_id == game.id).delete()
            db_session.query(Player).filter(Player.game_id == game.id).delete()
            db_session.delete(game)
        
        # Now delete the user
        db_session.delete(existing_user)
        db_session.commit()
    
    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    access_token = create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=30)
    )

    return {
        "id": user.id,
        "username": username,
        "token": access_token
    }

@pytest.fixture(scope="function")
def test_wordlist(db_session):
    """Create a test wordlist."""
    words = ["TEST", "WORD", "LIST"]
    for word in words:
        word_bytes = word.encode('utf-8')
        word_str = word_bytes.decode('utf-8')
        db_session.add(WordList(language="test", word=word_str))
    db_session.commit()
    return words

@pytest.fixture(scope="function")
def test_game_with_player(db_session, test_user):
    """Create a test game with a player."""
    # Create a game
    game = Game(
        id="test-game-id",
        creator_id=test_user["id"],
        state=json.dumps({
            "board": [[None]*15 for _ in range(15)],
            "language": "de",
            "phase": "not_started",
            "multipliers": {}
        }),
        status=GameStatus.SETUP,
        language="de",
        max_players=2
    )
    db_session.add(game)
    db_session.commit()
    db_session.refresh(game)
    
    # Create a player
    player = Player(
        game_id=game.id,
        user_id=test_user["id"],
        rack="ABCDEFG"
    )
    db_session.add(player)
    db_session.commit()
    db_session.refresh(player)
    
    return game, player

@pytest.fixture(scope="function")
def test_websocket_client(client, test_user, test_game_with_player, db_session):
    """Create a test client for WebSocket connections."""
    game, _ = test_game_with_player
    
    # Create a new client instance with authentication
    test_client = TestClient(app)
    test_client.headers = {
        "Authorization": f"Bearer {test_user['token']}",
        "Content-Type": "application/json"
    }
    
    # Override the database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_websocket_client2(client, test_user2, test_game_with_player, db_session):
    """Create a second test client for WebSocket connections."""
    game, _ = test_game_with_player
    
    # Create a new client instance with authentication
    test_client = TestClient(app)
    test_client.headers = {
        "Authorization": f"Bearer {test_user2['token']}",
        "Content-Type": "application/json"
    }
    
    # Override the database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def authenticated_client(client, test_user, db_session):
    """Create an authenticated test client."""
    # Create a new client instance with authentication
    test_client = TestClient(app)
    test_client.headers.update({
        "Authorization": f"Bearer {test_user['token']}",
        "Content-Type": "application/json"
    })
    
    # Override the database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def authenticated_client2(client, test_user2, db_session):
    """Create a second authenticated test client."""
    # Create a new client instance with authentication
    test_client = TestClient(app)
    test_client.headers.update({
        "Authorization": f"Bearer {test_user2['token']}",
        "Content-Type": "application/json"
    })
    
    # Override the database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

def read_file_utf8(file_path):
    """Helper function to read files with UTF-8 encoding."""
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            with codecs.open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    raise UnicodeDecodeError(f"Could not decode file {file_path} with any of the attempted encodings: {encodings}")




