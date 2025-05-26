import os
from dotenv import load_dotenv
import urllib.parse

# Load environment variables from .env file
load_dotenv()

# Database settings
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db:5432/wordbattle")

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
PERSISTENT_TOKEN_EXPIRE_DAYS = int(os.getenv("PERSISTENT_TOKEN_EXPIRE_DAYS", "30"))  # For "remember me"

# Email settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@wordbattle.com")
VERIFICATION_CODE_EXPIRE_MINUTES = int(os.getenv("VERIFICATION_CODE_EXPIRE_MINUTES", "10"))

# Game settings
DEFAULT_WORDLIST_PATH = os.getenv("DEFAULT_WORDLIST_PATH", "data/de_words.txt")
LETTER_POOL_SIZE = int(os.getenv("LETTER_POOL_SIZE", "7"))
GAME_INACTIVE_DAYS = int(os.getenv("GAME_INACTIVE_DAYS", "7"))

# API settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))  # Requests per minute
