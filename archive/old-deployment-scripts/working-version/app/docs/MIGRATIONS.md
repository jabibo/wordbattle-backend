# Database Migrations

This document describes how to manage database migrations for the WordBattle backend.

## Setup

1. Install Alembic:
```bash
pip install alembic
```

2. Initialize Alembic:
```bash
alembic init migrations
```

3. Edit `alembic.ini` to set the database URL:
```ini
sqlalchemy.url = sqlite:///./wordbattle.db
```

## Creating Migrations

To create a new migration:
```bash
alembic revision -m "description of changes"
```

## Running Migrations

To upgrade to the latest version:
```bash
alembic upgrade head
```

To downgrade to a previous version:
```bash
alembic downgrade -1
```

## First-time Setup

For initial database setup, run:
```bash
python -m app.create_tables
```

This should only be used for development or initial setup, not in production where migrations should be used instead.