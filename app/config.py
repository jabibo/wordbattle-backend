import os
from dotenv import load_dotenv
import urllib.parse
from typing import Dict, Any
from .cloud.providers import CloudProvider

# Load environment variables from .env file
load_dotenv()

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
TESTING = os.getenv("TESTING", "0") == "1"
DEBUG = os.getenv("DEBUG", "0") == "1"

# Cloud Provider Configuration
CLOUD_PROVIDER = CloudProvider(os.getenv("CLOUD_PROVIDER", "gcp"))

# Common Cloud Configuration
CLOUD_CONFIG: Dict[str, Any] = {
    "region": os.getenv("CLOUD_REGION", "europe-west1"),
    "bucket_name": os.getenv("STORAGE_BUCKET", "wordbattle-assets"),
}

# AWS-specific Configuration
if CLOUD_PROVIDER == CloudProvider.AWS:
    CLOUD_CONFIG.update({
        "cluster_name": os.getenv("AWS_ECS_CLUSTER", "wordbattle-cluster"),
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    })

# GCP-specific Configuration
elif CLOUD_PROVIDER == CloudProvider.GCP:
    CLOUD_CONFIG.update({
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "wordbattle-1748668162"),
        "service_account_key": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    })

# Database settings
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_NAME = os.environ.get("DB_NAME", "wordbattle")

# Cloud SQL settings for production/testing
CLOUD_SQL_CONNECTION_NAME = os.environ.get("CLOUD_SQL_CONNECTION_NAME", "wordbattle-1748668162:europe-west1:wordbattle-db")
CLOUD_SQL_DATABASE_NAME = os.environ.get("CLOUD_SQL_DATABASE_NAME", "wordbattle_test")

# Test database settings
TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "wordbattle_test")

def get_database_url(is_test=False):
    """Get database URL with proper encoding."""
    if CLOUD_PROVIDER == CloudProvider.AWS:
        # AWS RDS Connection
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = "wordbattle_test" if is_test else "wordbattle_db"
        db_user = os.getenv("DB_USER", "wordbattle")
        db_pass = os.getenv("DB_PASSWORD", "wordbattle123")
        return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    else:
        # GCP Cloud SQL Connection - using pg8000 with unix socket
        project_id = CLOUD_CONFIG["project_id"]
        instance_name = "wordbattle-db"
        db_name = "wordbattle_test" if is_test else "wordbattle_db"
        db_user = os.getenv("DB_USER", "wordbattle")
        db_pass = os.getenv("DB_PASSWORD", "wordbattle123")
        return f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}?unix_sock=/cloudsql/{project_id}:{CLOUD_CONFIG['region']}:{instance_name}"

# Use the function to get the main database URL
# Check if we're in testing mode to use test database
DATABASE_URL = get_database_url(TESTING)

# Security settings - CRITICAL: These must be set via environment variables in production
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if ENVIRONMENT == "production":
        raise ValueError("SECRET_KEY environment variable is required in production")
    else:
        print("⚠️  WARNING: Using default SECRET_KEY for development only!")
        SECRET_KEY = "dev-only-secret-key-change-in-production"

print(f"✅ Loaded SECRET_KEY starting with: {SECRET_KEY[:8]}...")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
PERSISTENT_TOKEN_EXPIRE_DAYS = int(os.getenv("PERSISTENT_TOKEN_EXPIRE_DAYS", "30"))  # For "remember me"

# Email settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.strato.de")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # SSL port
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    print("⚠️  SMTP_PASSWORD not set - email functionality disabled")
if not SMTP_USERNAME:
    print("⚠️  SMTP_USERNAME not set - email functionality disabled")

FROM_EMAIL = os.getenv("FROM_EMAIL")
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
if ENVIRONMENT == "production" and "*" in CORS_ORIGINS:
    raise ValueError("Wildcard CORS origins not allowed in production")

RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))  # Requests per minute

# Frontend URL settings
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")  # Default to frontend port
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")   # Default to backend port

# Contracts Configuration
CONTRACTS_DIR = os.environ.get("CONTRACTS_DIR", "/Users/janbinge/git/wordbattle/wordbattle-contracts")
ENABLE_CONTRACT_VALIDATION = os.environ.get("ENABLE_CONTRACT_VALIDATION", "true").lower() == "true"
CONTRACT_VALIDATION_STRICT = os.environ.get("CONTRACT_VALIDATION_STRICT", "false").lower() == "true"

# Validate contracts directory exists
if ENABLE_CONTRACT_VALIDATION and not os.path.exists(CONTRACTS_DIR):
    print(f"⚠️  WARNING: Contracts directory not found at {CONTRACTS_DIR}")
    print(f"   Contract validation will be disabled")
    ENABLE_CONTRACT_VALIDATION = False

print(f"📋 Contracts Configuration:")
print(f"  Directory: {CONTRACTS_DIR}")
print(f"  Validation Enabled: {ENABLE_CONTRACT_VALIDATION}")
print(f"  Strict Mode: {CONTRACT_VALIDATION_STRICT}")

# API Configuration
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Feature Flags
ENABLE_CONTRACT_VALIDATION = os.getenv("ENABLE_CONTRACT_VALIDATION", "1") == "1"

# Deployment Configuration
def get_deployment_config() -> Dict[str, Any]:
    if CLOUD_PROVIDER == CloudProvider.AWS:
        return {
            "service_name": "wordbattle-backend",
            "task_definition": "wordbattle-backend:latest",
            "container_port": 8000,
            "desired_count": 2,
            "cpu": "1024",
            "memory": "2048",
        }
    else:
        return {
            "service_name": "wordbattle-backend",
            "image": f"gcr.io/{CLOUD_CONFIG['project_id']}/wordbattle-backend:latest",
            "port": 8000,
            "cpu": "1000m",
            "memory": "2Gi",
            "min_instances": 0,
            "max_instances": 10,
        }

DEPLOYMENT_CONFIG = get_deployment_config()
