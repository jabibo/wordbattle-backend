#!/bin/bash
set -e

# Create database tables
echo "Creating database tables..."
python -m app.create_tables

# Start the application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000