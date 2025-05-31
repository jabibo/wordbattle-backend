#!/bin/bash

echo "Render Deployment - Non-AWS Alternative"
echo "======================================="

echo "Render deployment requires web interface setup."
echo "Here's what you need to do:"
echo ""

echo "1. Go to https://render.com and sign up/login"
echo "2. Click 'New +' -> 'Web Service'"
echo "3. Connect your GitHub repository"
echo "4. Configure the service:"
echo ""

# Create render.yaml for Infrastructure as Code
cat > render.yaml << 'EOF'
services:
  - type: web
    name: wordbattle-backend
    env: docker
    dockerfilePath: ./Dockerfile.prod
    plan: starter
    region: frankfurt
    envVars:
      - key: DB_HOST
        value: wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com
      - key: DB_NAME
        value: wordbattle
      - key: DB_USER
        value: postgres
      - key: DB_PASSWORD
        value: Wordbattle2024
      - key: PORT
        value: 8000
    healthCheckPath: /health
    autoDeploy: true
EOF

echo "Configuration saved to render.yaml"
echo ""
echo "Manual Setup Instructions:"
echo "=========================="
echo ""
echo "Service Settings:"
echo "- Name: wordbattle-backend"
echo "- Environment: Docker"
echo "- Dockerfile Path: ./Dockerfile.prod"
echo "- Plan: Starter ($7/month)"
echo "- Region: Frankfurt"
echo ""
echo "Environment Variables:"
echo "- DB_HOST = wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com"
echo "- DB_NAME = wordbattle"
echo "- DB_USER = postgres"
echo "- DB_PASSWORD = Wordbattle2024"
echo "- PORT = 8000"
echo ""
echo "Advanced Settings:"
echo "- Health Check Path: /health"
echo "- Auto-Deploy: Yes"
echo ""
echo "Alternative: Use render.yaml"
echo "============================"
echo "1. Commit render.yaml to your repository"
echo "2. In Render dashboard, click 'New +' -> 'Blueprint'"
echo "3. Connect repository and select render.yaml"
echo "4. Deploy automatically"
echo ""
echo "After deployment, your app will be available at:"
echo "https://wordbattle-backend.onrender.com"
echo ""
echo "Test endpoints:"
echo "- Health: https://wordbattle-backend.onrender.com/health"
echo "- Debug: https://wordbattle-backend.onrender.com/debug/tokens" 