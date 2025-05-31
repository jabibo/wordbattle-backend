# PostgreSQL Migration Guide

This guide explains how to migrate the WordBattle backend from SQLite to PostgreSQL.

## Prerequisites

- PostgreSQL installed and running
- psycopg2-binary Python package installed

## Steps to Migrate

1. **Install PostgreSQL Driver**

```bash
pip install psycopg2-binary
```

2. **Create PostgreSQL Database**

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE wordbattle;

# Exit
\q
```

3. **Update Environment Variables**

Edit your `.env` file to use PostgreSQL:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/wordbattle
```

4. **Initialize Alembic**

```bash
# Install Alembic if not already installed
pip install alembic

# Initialize Alembic
alembic init migrations
```

5. **Configure Alembic**

Update `migrations/env.py` to include:

```python
from app.config import DATABASE_URL
from app.models import Base, User, Game, Player, Move

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", DATABASE_URL)
```

6. **Create Initial Migration**

```bash
alembic revision --autogenerate -m "initial"
```

7. **Apply Migration**

```bash
alembic upgrade head
```

8. **Migrate Data (Optional)**

If you have existing data in SQLite that you want to migrate:

```bash
# Export data from SQLite (example using a script)
python scripts/export_data.py

# Import data to PostgreSQL
python scripts/import_data.py
```

9. **Test the Connection**

```bash
# Run the application with PostgreSQL
uvicorn app.main:app --reload
```

## Troubleshooting

### Import Errors

If you encounter import errors with `Base` or models:

1. Make sure `app/models/__init__.py` re-exports all models:
```python
from app.database import Base
from app.models.user import User
from app.models.game import Game
from app.models.player import Player
from app.models.move import Move

__all__ = ['Base', 'User', 'Game', 'Player', 'Move']
```

2. Ensure all models are imported in `migrations/env.py`:
```python
from app.models import Base, User, Game, Player, Move
```

### Connection Issues

If you have connection issues:

1. Verify PostgreSQL is running:
```bash
pg_isready
```

2. Check connection parameters:
```bash
psql -U postgres -h localhost -p 5432 -d wordbattle
```

3. Ensure your firewall allows connections to PostgreSQL

### Migration Errors

If you encounter migration errors:

1. Drop and recreate the database:
```bash
dropdb wordbattle
createdb wordbattle
```

2. Re-run migrations:
```bash
alembic upgrade head
```