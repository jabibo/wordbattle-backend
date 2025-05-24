import os
from dotenv import load_dotenv
import urllib.parse

# Load environment variables from .env file
load_dotenv()

# Database settings
# Get database host from environment or use default
DB_HOST = os.environ.get("DB_HOST", "localhost")  # Default to localhost for local development
#DB_HOST = os.environ.get("DB_HOST", "host.docker.internal")  # Default to localhost for local development

DB_PORT = os.environ.get("DB_PORT", "5432")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "delta42%")
DB_NAME = os.environ.get("DB_NAME", "wordbattle")

# URL encode the password to handle special characters
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

# Construct database URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Security settings
SECRET_KEY = os.environ.get("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Game settings
DEFAULT_WORDLIST_PATH = os.environ.get("DEFAULT_WORDLIST_PATH", "data/de_words.txt")
LETTER_POOL_SIZE = int(os.environ.get("LETTER_POOL_SIZE", "7"))
GAME_INACTIVE_DAYS = int(os.environ.get("GAME_INACTIVE_DAYS", "7"))

# API settings
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "60"))  # Requests per minute
