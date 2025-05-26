from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_database_url
import os

# Get database URL based on environment
DATABASE_URL = get_database_url(is_test=os.getenv("TESTING") == "1")

# Create database engine with URL from config
engine = create_engine(
    DATABASE_URL,
    # Only use check_same_thread for SQLite
    connect_args={} if not DATABASE_URL.startswith("sqlite") else {"check_same_thread": False}
)
print(f"Using database: {DATABASE_URL}")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
