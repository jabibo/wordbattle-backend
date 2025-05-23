#!/bin/bash
set -e

host="db"
until PGPASSWORD=postgres psql -h "System.Management.Automation.Internal.Host.InternalHost" -U "postgres" -c '\q'; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Postgres is up - executing command"
python -m app.create_tables
uvicorn app.main:app --host 0.0.0.0 --port 8000