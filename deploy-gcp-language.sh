#!/bin/bash

echo "🚀 Google Cloud Run Deployment - Language Preference System"
echo "=========================================================="

# Configuration - Using the actual project ID
PROJECT_ID="wordbattle-1748668162"
SERVICE_NAME="wordbattle-backend"
REGION="europe-west1" 
IMAGE_TAG="language-v1.0"

echo "This script will deploy the new language preference system to Google Cloud Run"
echo "Project: $PROJECT_ID"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI not found. Please install it first:"
    echo "   curl https://sdk.cloud.google.com | bash"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "🔐 Please login to Google Cloud:"
    gcloud auth login
fi

# Set project
echo "📋 Setting up Google Cloud project..."
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Prepare Dockerfile for Cloud Build
echo "📝 Preparing Dockerfile for Cloud Build..."
cp Dockerfile.cloudrun Dockerfile

# Build and deploy using Cloud Build (simplified)
echo "🏗️ Building Docker image with Cloud Build..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/wordbattle-backend:$IMAGE_TAG .

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    rm -f Dockerfile  # Clean up
    exit 1
fi

# Clean up temporary Dockerfile
rm -f Dockerfile

echo "🚀 Deploying to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image=gcr.io/$PROJECT_ID/wordbattle-backend:$IMAGE_TAG \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --port=8000 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --set-env-vars="DB_HOST=35.187.90.105,DB_NAME=wordbattle_db,DB_USER=postgres,DB_PASSWORD=Wordbattle2024" \
  --max-instances=10 \
  --min-instances=1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
    
    echo "🌐 Application URL: $SERVICE_URL"
    echo "🏥 Health check: $SERVICE_URL/health"
    echo "📖 API Docs: $SERVICE_URL/docs"
    
    echo ""
    echo "🧪 Testing the new language endpoints..."
    sleep 15
    
    # Test health endpoint
    echo "Testing health endpoint..."
    if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
        echo "✅ Health check passed!"
    else
        echo "❌ Health check failed"
    fi
    
    # Test language endpoint (should require auth)
    echo "Testing language endpoint..."
    RESPONSE=$(curl -s "$SERVICE_URL/users/language")
    if echo "$RESPONSE" | grep -q "Not authenticated"; then
        echo "✅ Language endpoint working (requires authentication as expected)!"
    else
        echo "❌ Language endpoint test failed: $RESPONSE"
    fi
    
    # Show service info
    echo ""
    echo "📊 Service Information:"
    gcloud run services describe $SERVICE_NAME --region=$REGION --format="table(metadata.name,status.url,status.latestReadyRevisionName)"
    
    echo ""
    echo "🎉 Language Preference System deployed to Google Cloud!"
    echo ""
    echo "🔧 New Features Available:"
    echo "  - GET $SERVICE_URL/users/language - Get user language preference"
    echo "  - PUT $SERVICE_URL/users/language - Update user language preference"  
    echo "  - Enhanced login responses with language information"
    echo "  - Automatic database migration for language field"
    echo ""
    echo "📱 Frontend can now use these endpoints for internationalization!"
    
else
    echo "❌ Deployment failed!"
    echo ""
    echo "Check the logs with:"
    echo "  gcloud logs read --service=$SERVICE_NAME --region=$REGION"
    exit 1
fi 