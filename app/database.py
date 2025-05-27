from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL, get_database_url
import os

# Get database URL based on environment
# Use DATABASE_URL directly if not testing, otherwise use get_database_url for test database
if os.getenv("TESTING") == "1":
    DATABASE_URL = get_database_url(is_test=True)
# DATABASE_URL is already set from config.py which respects environment variables

# Create database engine with URL from config
engine = create_engine(
    DATABASE_URL,
    # Only use check_same_thread for SQLite
    connect_args={} if not DATABASE_URL.startswith("sqlite") else {"check_same_thread": False}
)
print(f"Using database: {DATABASE_URL}")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
