from sqlalchemy.orm import Session
from app.database import SessionLocal

def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 