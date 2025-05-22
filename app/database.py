from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

# Create database engine with URL from config
engine = create_engine(
    DATABASE_URL,
    # Only use check_same_thread for SQLite
    connect_args={} if not DATABASE_URL.startswith("sqlite") else {"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()