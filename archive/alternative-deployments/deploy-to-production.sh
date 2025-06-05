#!/bin/bash

# Production Deployment Script for WordBattle Backend
# Language Preference Management System Deployment

echo "🚀 Starting WordBattle Backend Production Deployment..."

# Pull latest code
echo "📥 Pulling latest code from production branch..."
git pull origin production

# Stop current containers
echo "🛑 Stopping current containers..."
docker-compose down

# Build new image
echo "🔨 Building new Docker image..."
docker-compose build app

# Start containers with new image
echo "▶️ Starting containers with new image..."
docker-compose up -d

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 15

# Check if migration ran successfully
echo "✅ Checking migration status..."
docker-compose logs app | grep -i migration

# Verify endpoints are working
echo "🧪 Testing API endpoints..."
echo "Testing health endpoint:"
curl -s http://localhost:8000/health

echo -e "\nTesting language endpoint (should require auth):"
curl -s http://localhost:8000/users/language

# Show container status
echo -e "\n📊 Container Status:"
docker-compose ps

echo -e "\n✅ Deployment Complete!"
echo "🔧 New Features Deployed:"
echo "  - User language preference storage"
echo "  - GET /users/language endpoint"
echo "  - PUT /users/language endpoint"  
echo "  - Enhanced login responses with language"
echo "  - Automatic database migration"

echo -e "\n📖 API Documentation: http://your-domain.com/docs" 