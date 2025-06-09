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

# Security settings - CRITICAL: These must be set via environment variables in production
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError("SECRET_KEY environment variable is required in production")
    else:
        print("⚠️  WARNING: Using default SECRET_KEY for development only!")
        SECRET_KEY = "dev-only-secret-key-change-in-production"

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
PERSISTENT_TOKEN_EXPIRE_DAYS = int(os.getenv("PERSISTENT_TOKEN_EXPIRE_DAYS", "30"))  # For "remember me"

# Email settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.strato.de")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # SSL port
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "jan@binge-dev.de")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    print("⚠️  SMTP_PASSWORD not set - email functionality disabled")

FROM_EMAIL = os.getenv("FROM_EMAIL", "jan@binge-dev.de")
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
VERIFICATION_CODE_EXPIRE_MINUTES = int(os.getenv("VERIFICATION_CODE_EXPIRE_MINUTES", "10"))

# Mobile app settings
MOBILE_DEEP_LINK_SCHEME = os.getenv("MOBILE_DEEP_LINK_SCHEME", "wordbattle")
ENABLE_PUSH_NOTIFICATIONS = os.getenv("ENABLE_PUSH_NOTIFICATIONS", "false").lower() == "true"
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")  # For Firebase push notifications

# Game settings
DEFAULT_WORDLIST_PATH = os.getenv("DEFAULT_WORDLIST_PATH", "data/de_words.txt")
LETTER_POOL_SIZE = int(os.getenv("LETTER_POOL_SIZE", "7"))
GAME_INACTIVE_DAYS = int(os.getenv("GAME_INACTIVE_DAYS", "7"))

# API settings - CORS origins should be configured per environment
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://localhost:3000").split(",")
# Temporarily allow wildcard for mobile app testing
# if os.getenv("ENVIRONMENT") == "production" and "*" in CORS_ORIGINS:
#     raise ValueError("Wildcard CORS origins not allowed in production")

RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))  # Requests per minute

# Frontend URL settings
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")  # Default to frontend port
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")   # Default to backend port
