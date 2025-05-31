#!/bin/bash

echo "Railway Deployment - Non-AWS Alternative"
echo "========================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway:"
    railway login
fi

# Create railway.json configuration
cat > railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.prod"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "ON_FAILURE"
  }
}
EOF

# Create environment variables file
cat > .env.railway << 'EOF'
DB_HOST=wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com
DB_NAME=wordbattle
DB_USER=postgres
DB_PASSWORD=Wordbattle2024
PORT=8000
EOF

echo "Creating Railway project..."
railway init

echo "Setting environment variables..."
railway variables set DB_HOST=wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com
railway variables set DB_NAME=wordbattle
railway variables set DB_USER=postgres
railway variables set DB_PASSWORD=Wordbattle2024
railway variables set PORT=8000

echo "Deploying to Railway..."
railway up

echo ""
echo "Deployment completed!"
echo "Getting service URL..."

# Get the service URL
SERVICE_URL=$(railway status --json | grep -o '"url":"[^"]*"' | cut -d'"' -f4)

if [ -n "$SERVICE_URL" ]; then
    echo "Application URL: $SERVICE_URL"
    echo "Health check: $SERVICE_URL/health"
    echo "Debug tokens: $SERVICE_URL/debug/tokens"
else
    echo "Service URL not available yet. Check Railway dashboard:"
    echo "https://railway.app/dashboard"
fi

echo ""
echo "Railway deployment complete!"
echo "Your application is now running outside AWS!"

# Clean up
rm -f railway.json .env.railway 