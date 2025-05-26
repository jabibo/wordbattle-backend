#!/bin/bash
set -e

host="$1"
until PGPASSWORD=postgres psql -h "$host" -U "postgres" -c '\q'; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Postgres is up - executing command"
python -m app.create_tables
pytest -v