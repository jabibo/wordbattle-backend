import os
from sqlalchemy import create_engine, text

# Print the DATABASE_URL
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL')}")

# Create engine
engine = create_engine(os.environ.get('DATABASE_URL'))

# Test connection
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
