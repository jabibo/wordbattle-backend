from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL, get_database_url, CLOUD_PROVIDER
from app.cloud.providers import CloudProvider
import os

# Get database URL based on environment
# Use DATABASE_URL directly if not testing, otherwise use get_database_url for test database
if os.getenv("TESTING") == "1":
    DATABASE_URL = get_database_url(is_test=True)
# DATABASE_URL is already set from config.py which respects environment variables

# For GCP Cloud SQL, use the Cloud SQL Python Connector
if CLOUD_PROVIDER == CloudProvider.GCP and "unix_sock" in DATABASE_URL:
    from google.cloud.sql.connector import Connector
    import asyncpg
    import re
    
    # Extract connection details from URL
    match = re.match(r'postgresql\+pg8000://([^:]+):([^@]+)@/([^?]+)\?unix_sock=/cloudsql/(.+)', DATABASE_URL)
    if match:
        user, password, db_name, instance_connection_name = match.groups()
        
        # Create a custom connection function using Cloud SQL Connector
        def getconn():
            connector = Connector()
            conn = connector.connect(
                instance_connection_name,
                "pg8000",
                user=user,
                password=password,
                db=db_name
            )
            return conn
        
        # Create engine with custom connection function
        engine = create_engine(
            "postgresql+pg8000://",
            creator=getconn,
        )
        print(f"Using Cloud SQL Connector for: {instance_connection_name}/{db_name}")
    else:
        # Fallback to original URL
        engine = create_engine(DATABASE_URL)
        print(f"Using database: {DATABASE_URL}")
else:
    # Create database engine with URL from config
    engine = create_engine(
        DATABASE_URL,
        # Only use check_same_thread for SQLite
        connect_args={} if not DATABASE_URL.startswith("sqlite") else {"check_same_thread": False}
    )
    print(f"Using database: {DATABASE_URL}")

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
