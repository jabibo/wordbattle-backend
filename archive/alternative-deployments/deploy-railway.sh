#!/bin/bash

echo "Railway Deployment - Google Cloud SQL Backend"
echo "========================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway:"
    railway login
fi

echo "📋 Setting up Railway project..."

# Create or select project
railway project new --name wordbattle-backend || railway project

echo "🔧 Setting environment variables..."

# Database settings (using Google Cloud SQL)
DB_HOST=35.187.90.105
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=Wordbattle2024
DB_NAME=wordbattle_db

# Set all environment variables
railway variables set SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
railway variables set ALGORITHM=HS256
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES=30
railway variables set DB_HOST=$DB_HOST
railway variables set DB_PORT=$DB_PORT
railway variables set DB_USER=$DB_USER
railway variables set DB_PASSWORD=$DB_PASSWORD
railway variables set DB_NAME=$DB_NAME
railway variables set SMTP_SERVER=smtp.strato.de
railway variables set SMTP_PORT=465
railway variables set SMTP_USERNAME=jan@binge-dev.de
railway variables set SMTP_PASSWORD=q2NvW4J1%tcAyJSg8
railway variables set FROM_EMAIL=jan@binge-dev.de
railway variables set SMTP_USE_SSL=true
railway variables set VERIFICATION_CODE_EXPIRE_MINUTES=10
railway variables set DEFAULT_WORDLIST_PATH=data/de_words.txt
railway variables set LETTER_POOL_SIZE=7
railway variables set GAME_INACTIVE_DAYS=7
railway variables set CORS_ORIGINS=*
railway variables set RATE_LIMIT=60

echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Summary:"
echo "- Platform: Railway"
echo "- Database: Google Cloud SQL PostgreSQL"
echo "- DB_HOST = $DB_HOST"
echo "- DB_NAME = $DB_NAME"
echo ""
echo "🔗 View your deployment:"
railway domain
echo ""
echo "📝 View logs:"
echo "   railway logs"
echo ""
echo "Your application is now running with Google Cloud SQL!"

# Clean up
rm -f railway.json .env.railway 