#!/bin/bash

echo "Google Cloud Run Deployment - Non-AWS Alternative"
echo "================================================="

# Configuration
PROJECT_ID="wordbattle-project"
SERVICE_NAME="wordbattle-backend"
REGION="europe-west1"
IMAGE_TAG="working-exact"

echo "This script will deploy your WordBattle backend to Google Cloud Run"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Installing Google Cloud CLI..."
    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL
    echo "Please restart your terminal and run this script again."
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Please login to Google Cloud:"
    gcloud auth login
fi

# Set or create project
echo "Setting up Google Cloud project..."
gcloud config set project $PROJECT_ID 2>/dev/null || {
    echo "Project $PROJECT_ID doesn't exist. Creating it..."
    gcloud projects create $PROJECT_ID --name="WordBattle Project"
    gcloud config set project $PROJECT_ID
    
    echo "Please enable billing for this project in the Google Cloud Console:"
    echo "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
    echo ""
    read -p "Press Enter after enabling billing..."
}

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Set region
gcloud config set run/region $REGION

# Since we're using an AWS ECR image, we need to pull it and push to Google Container Registry
echo "Setting up container image..."

# First, let's try to use the image directly from AWS ECR
echo "Attempting to deploy directly from AWS ECR..."

# Deploy to Cloud Run
echo "Deploying to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image=598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:$IMAGE_TAG \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --port=8000 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --set-env-vars="DB_HOST=wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com,DB_NAME=wordbattle,DB_USER=postgres,DB_PASSWORD=Wordbattle2024" \
  --max-instances=10 \
  --min-instances=0

if [ $? -eq 0 ]; then
    echo ""
    echo "Deployment successful!"
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
    
    echo "Application URL: $SERVICE_URL"
    echo "Health check: $SERVICE_URL/health"
    echo "Debug tokens: $SERVICE_URL/debug/tokens"
    
    echo ""
    echo "Testing the deployment..."
    sleep 10
    
    # Test health endpoint
    if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
        echo "✅ Health check passed!"
    else
        echo "❌ Health check failed - but service is deployed"
    fi
    
    # Test debug endpoint
    if curl -f "$SERVICE_URL/debug/tokens" > /dev/null 2>&1; then
        echo "✅ Debug tokens endpoint working!"
        echo ""
        echo "🎉 Google Cloud Run deployment complete!"
        echo "Your application is now running outside AWS!"
    else
        echo "❌ Debug tokens endpoint not responding yet"
        echo "The service may still be starting up..."
    fi
    
else
    echo "❌ Deployment failed. This might be due to ECR access issues."
    echo ""
    echo "Alternative: Push image to Google Container Registry"
    echo "=================================================="
    echo ""
    echo "1. Pull the image locally:"
    echo "   docker pull 598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:$IMAGE_TAG"
    echo ""
    echo "2. Tag for Google Container Registry:"
    echo "   docker tag 598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:$IMAGE_TAG gcr.io/$PROJECT_ID/wordbattle-backend:$IMAGE_TAG"
    echo ""
    echo "3. Push to GCR:"
    echo "   docker push gcr.io/$PROJECT_ID/wordbattle-backend:$IMAGE_TAG"
    echo ""
    echo "4. Deploy from GCR:"
    echo "   gcloud run deploy $SERVICE_NAME --image=gcr.io/$PROJECT_ID/wordbattle-backend:$IMAGE_TAG --platform=managed --region=$REGION --allow-unauthenticated --port=8000 --set-env-vars=\"DB_HOST=wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com,DB_NAME=wordbattle,DB_USER=postgres,DB_PASSWORD=Wordbattle2024\""
fi 