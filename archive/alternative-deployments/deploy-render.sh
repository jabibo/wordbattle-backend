#!/bin/bash

echo "Render Deployment - Google Cloud SQL Backend"

# Check if we have the render API key
if [ -z "$RENDER_API_KEY" ]; then
    echo "❌ RENDER_API_KEY environment variable not set"
    echo "Please get your API key from: https://dashboard.render.com/account/api-keys"
    echo "Then run: export RENDER_API_KEY=your_api_key_here"
    exit 1
fi

echo "📋 Creating Render service configuration..."

# Create render.yaml configuration
cat > render.yaml << 'EOF'
services:
  - type: web
    name: wordbattle-backend
    env: docker
    dockerfilePath: ./Dockerfile.cloudrun
    region: oregon
    plan: starter
    branch: production
    buildCommand: ""
    startCommand: ""
    envVars:
      - key: DB_HOST
        value: 35.187.90.105
      - key: DB_PORT
        value: 5432
      - key: DB_USER
        value: postgres
      - key: DB_PASSWORD
        value: Wordbattle2024
      - key: DB_NAME
        value: wordbattle_db
      - key: SECRET_KEY
        value: 09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
      - key: ALGORITHM
        value: HS256
      - key: ACCESS_TOKEN_EXPIRE_MINUTES
        value: 30
      - key: SMTP_SERVER
        value: smtp.strato.de
      - key: SMTP_PORT
        value: 465
      - key: SMTP_USERNAME
        value: jan@binge-dev.de
      - key: SMTP_PASSWORD
        value: q2NvW4J1%tcAyJSg8
      - key: FROM_EMAIL
        value: jan@binge-dev.de
      - key: SMTP_USE_SSL
        value: true
      - key: VERIFICATION_CODE_EXPIRE_MINUTES
        value: 10
      - key: DEFAULT_WORDLIST_PATH
        value: data/de_words.txt
      - key: LETTER_POOL_SIZE
        value: 7
      - key: GAME_INACTIVE_DAYS
        value: 7
      - key: CORS_ORIGINS
        value: "*"
      - key: RATE_LIMIT
        value: 60
EOF

echo "🚀 Deploying to Render..."

# Note: Render deployment typically uses Git integration
echo "📝 Configuration created in render.yaml"
echo ""
echo "✅ Next steps:"
echo "1. Commit and push the render.yaml file to your repository"
echo "2. Go to Render Dashboard: https://dashboard.render.com"
echo "3. Connect your repository and deploy using the render.yaml configuration"
echo ""
echo "📋 Summary:"
echo "- Platform: Render"
echo "- Database: Google Cloud SQL PostgreSQL"
echo "- DB_HOST = 35.187.90.105"
echo "- DB_NAME = wordbattle_db"
echo ""
echo "Your application will run with Google Cloud SQL!" 