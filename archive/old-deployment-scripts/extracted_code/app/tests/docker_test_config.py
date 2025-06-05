import os
from app.config import get_database_url

# Set testing environment variables
os.environ["TESTING"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

# Test database settings are handled by app/config.py
# Override database URL for tests in Docker to connect to host PostgreSQL
os.environ["DATABASE_URL"] = get_database_url(is_test=True)
