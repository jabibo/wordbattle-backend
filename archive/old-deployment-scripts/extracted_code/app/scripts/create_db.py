import sqlalchemy
from sqlalchemy_utils import database_exists, create_database
import sys
import os

# Import the centralized config
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# PostgreSQL connection URL without database name
engine_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
full_url = f"{engine_url}/{DB_NAME}"

print(f"Using database connection: {engine_url}")

# Create engine without database name to connect to PostgreSQL server
engine = sqlalchemy.create_engine(engine_url)

# Create database if it doesn't exist
if not database_exists(full_url):
    try:
        create_database(full_url)
        print(f"Database '{DB_NAME}' created successfully")
    except Exception as e:
        print(f"Error creating database: {e}")
else:
    print(f"Database '{DB_NAME}' already exists")
