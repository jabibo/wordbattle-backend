import sqlalchemy
from sqlalchemy_utils import database_exists, create_database

# PostgreSQL connection URL without database name
engine_url = "postgresql://postgres:postgres@localhost:5432"
db_name = "wordbattle"
full_url = f"{engine_url}/{db_name}"

# Create engine without database name to connect to PostgreSQL server
engine = sqlalchemy.create_engine(engine_url)

# Create database if it doesn't exist
if not database_exists('xx'):
    try:
        create_database('xx')
        print(f"Database '{db_name}' created successfully")
    except Exception as e:
        print(f"Error creating database: {e}")
else:
    print(f"Database '{db_name}' already exists")