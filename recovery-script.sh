#!/bin/bash

# Emergency Recovery Script for wordbattle-backend
# Run this on the production server when SSH is available

set -e

cd /home/wordbattle/wordbattle

echo "=== Wordbattle Backend Recovery ==="
echo ""

# Stop and remove any existing backend container
echo "1. Stopping old container..."
docker stop wordbattle-backend 2>/dev/null || true
docker rm wordbattle-backend 2>/dev/null || true

# Find the correct database container name
DB_CONTAINER=$(docker ps | grep -E 'postgres|wordbattle-db' | awk '{print $NF}' | head -1)
echo "2. Found database container: $DB_CONTAINER"

# Get the correct network
NETWORK=$(docker network ls | grep wordbattle-net | awk '{print $2}')
echo "3. Using network: $NETWORK"

# Start new container with updated image
echo "4. Starting new container..."
docker run -d \
  --name wordbattle-backend \
  --restart unless-stopped \
  --network "$NETWORK" \
  -p 127.0.0.1:8000:8000 \
  --env-file .env \
  -e DB_HOST="$DB_CONTAINER" \
  -e DB_PORT=5432 \
  -v $(pwd)/logs/app:/app/logs \
  wordbattle-backend:latest

echo "5. Waiting for startup (20 seconds)..."
sleep 20

echo ""
echo "=== Container Status ==="
docker ps --filter "name=wordbattle-backend" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

echo ""
echo "=== Recent Logs ==="
docker logs --tail 30 wordbattle-backend 2>&1 | grep -v DEBUG | tail -20

echo ""
echo "=== Health Check ==="
curl -s http://localhost:8000/health | head -5 || echo "Health endpoint not responding yet"

echo ""
echo "=== Checking for Wordlist Errors ==="
docker logs wordbattle-backend 2>&1 | grep -i "wordlist.*de" | tail -5

echo ""
echo "Done! Check https://wordbattle2.de/health"
