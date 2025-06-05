from datetime import datetime, timezone
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Add this to your app/database.py file
@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('SELECT 1')
    cursor.close()

# Add this to your app/models.py file
def utcnow():
    return datetime.now(timezone.utc)
