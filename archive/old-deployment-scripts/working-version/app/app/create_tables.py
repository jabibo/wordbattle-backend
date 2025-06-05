from app.database import engine, Base
from app.models import User, Game, Player, Move
import argparse

def create_all_tables():
    """Create all database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

def drop_all_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database table management")
    parser.add_argument("--drop", action="store_true", help="Drop all tables before creating them")
    parser.add_argument("--create", action="store_true", help="Create all tables")
    args = parser.parse_args()
    
    if args.drop:
        drop_all_tables()
    
    if args.create or not args.drop:
        create_all_tables()