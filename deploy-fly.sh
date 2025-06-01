#!/bin/bash

echo "Fly.io Deployment - Google Cloud SQL Backend"
echo "======================================="

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Fly CLI not found. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "🔐 Please login to Fly.io:"
    flyctl auth login
fi

echo "📋 Setting up Fly.io project..."

# Initialize fly app if not exists
if [ ! -f "fly.toml" ]; then
    flyctl launch --no-deploy --generate-name --region fra
fi

echo "🔧 Setting environment variables..."

# Database settings (using Google Cloud SQL)
flyctl secrets set DB_HOST=35.187.90.105
flyctl secrets set DB_PORT=5432
flyctl secrets set DB_USER=postgres
flyctl secrets set DB_PASSWORD=Wordbattle2024
flyctl secrets set DB_NAME=wordbattle_db

# Application settings
flyctl secrets set SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
flyctl secrets set ALGORITHM=HS256
flyctl secrets set ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email settings
flyctl secrets set SMTP_SERVER=smtp.strato.de
flyctl secrets set SMTP_PORT=465
flyctl secrets set SMTP_USERNAME=jan@binge-dev.de
flyctl secrets set SMTP_PASSWORD=q2NvW4J1%tcAyJSg8
flyctl secrets set FROM_EMAIL=jan@binge-dev.de
flyctl secrets set SMTP_USE_SSL=true
flyctl secrets set VERIFICATION_CODE_EXPIRE_MINUTES=10

# Game settings
flyctl secrets set DEFAULT_WORDLIST_PATH=data/de_words.txt
flyctl secrets set LETTER_POOL_SIZE=7
flyctl secrets set GAME_INACTIVE_DAYS=7
flyctl secrets set CORS_ORIGINS="*"
flyctl secrets set RATE_LIMIT=60

echo "🚀 Deploying to Fly.io..."
flyctl deploy

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Summary:"
echo "- Platform: Fly.io"
echo "- Database: Google Cloud SQL PostgreSQL"
echo "- DB_HOST = 35.187.90.105"
echo "- DB_NAME = wordbattle_db"
echo ""
echo "🔗 View your deployment:"
flyctl status
echo ""
echo "📝 View logs:"
echo "   flyctl logs"
echo ""
echo "Your application is now running with Google Cloud SQL!" 