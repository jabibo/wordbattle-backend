#!/bin/bash
# Docker-based Test Execution Script (with password authentication)
# Usage: ./scripts/run-tests-docker.sh [options]
# This script runs tests inside Docker containers with proper password auth

set -e

echo "🐳 WordBattle Backend Test Suite (Docker)"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse arguments
RUN_COVERAGE=false
TEST_PATH="tests/"

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            RUN_COVERAGE=true
            shift
            ;;
        --path)
            TEST_PATH="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./scripts/run-tests-docker.sh [options]"
            echo ""
            echo "Options:"
            echo "  --coverage       Enable coverage reporting"
            echo "  --path <path>    Run specific test path"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if test database is running
echo "🔍 Checking test database..."
if ! docker ps | grep -q wordbattle-test-db; then
    echo -e "${YELLOW}⚠️  Test database not running. Starting...${NC}"
    docker-compose -f docker-compose.test.yml up -d
    echo "⏳ Waiting for database to be ready..."
    sleep 8
    echo -e "${GREEN}✅ Database ready${NC}"
else
    echo -e "${GREEN}✅ Database already running${NC}"
fi

# Build pytest command
PYTEST_CMD="pytest $TEST_PATH -v --color=yes"

if [ "$RUN_COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=html --cov-report=term"
fi

echo ""
echo "🚀 Running tests in Docker container..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run tests in Docker with password authentication
docker run --rm \
    --network wordbattle-backend_test-network \
    -v "$(pwd):/app" \
    -w /app \
    -e TESTING=1 \
    -e ENVIRONMENT=test \
    -e DB_HOST=postgres-test \
    -e DB_PORT=5432 \
    -e DB_NAME=wordbattle_test \
    -e DB_USER=wordbattle_test \
    -e DB_PASSWORD=test_password_123 \
    -e CLOUD_PROVIDER=gcp \
    -e GOOGLE_CLOUD_PROJECT=wordbattle-secure \
    -e USE_CLOUD_SQL=false \
    -e SECRET_KEY=test-secret-key-not-for-production \
    -e ALGORITHM=HS256 \
    -e CORS_ORIGINS='["http://localhost:3000"]' \
    python:3.12-slim \
    bash -c "
        echo '📦 Installing dependencies...' && \
        pip install -q -r requirements.txt && \
        pip install -q -r requirements-test.txt && \
        echo '🧪 Running tests...' && \
        echo '' && \
        PYTHONPATH=/app $PYTEST_CMD
    "

EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    
    if [ "$RUN_COVERAGE" = true ]; then
        echo ""
        echo "📊 Coverage report available at: htmlcov/index.html"
    fi
else
    echo -e "${RED}❌ Some tests failed!${NC}"
fi

exit $EXIT_CODE

