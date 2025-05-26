import os
from dotenv import load_dotenv
import urllib.parse

# Load environment variables from .env file
load_dotenv()

# Database settings
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_NAME = os.environ.get("DB_NAME", "wordbattle")

# Test database settings
TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "wordbattle_test")

def get_database_url(is_test=False):
    """Get database URL with proper encoding."""
    db_name = TEST_DB_NAME if is_test else DB_NAME
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"

# Use the function to get the main database URL
DATABASE_URL = os.environ.get("DATABASE_URL", get_database_url())

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Game settings
DEFAULT_WORDLIST_PATH = os.getenv("DEFAULT_WORDLIST_PATH", "data/de_words.txt")
LETTER_POOL_SIZE = int(os.getenv("LETTER_POOL_SIZE", "7"))
GAME_INACTIVE_DAYS = int(os.getenv("GAME_INACTIVE_DAYS", "7"))

# API settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))  # Requests per minute
