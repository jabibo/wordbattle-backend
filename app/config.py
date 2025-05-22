import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database settings
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wordbattle.db")
DATABASE_URL="postgresql://postgres:delta42%@localhost:5432/wordbattle"

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