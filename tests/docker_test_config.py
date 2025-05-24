import os

# Set testing environment variable
os.environ["TESTING"] = "1"

# Override database URL for tests in Docker to connect to host PostgreSQL
# 'host.docker.internal' is a special DNS name that resolves to the host machine
os.environ["DATABASE_URL"] = "postgresql://postgres:delta42%@host.docker.internal:5432/wordbattle_test"
