#!/bin/bash

echo "Google Cloud Run - Simple Deployment"
echo "===================================="

# Configuration
PROJECT_ID="wordbattle-$(date +%s)"
SERVICE_NAME="wordbattle-backend"
REGION="europe-west1"

echo "This will deploy your app to Google Cloud Run using local Docker build"
echo "Project ID: $PROJECT_ID"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Google Cloud CLI not found. Installing..."
    echo "Please run: curl https://sdk.cloud.google.com | bash"
    echo "Then restart your terminal and run this script again."
    exit 1
fi

# Login if needed
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Please login to Google Cloud:"
    gcloud auth login
fi

# Create project
echo "Creating Google Cloud project..."
gcloud projects create $PROJECT_ID --name="WordBattle Backend" || {
    echo "Project creation failed. Using existing project or trying with different name..."
    PROJECT_ID="wordbattle-backend-$(date +%s)"
    gcloud projects create $PROJECT_ID --name="WordBattle Backend"
}

# Set project
gcloud config set project $PROJECT_ID

echo ""
echo "⚠️  IMPORTANT: Enable billing for this project"
echo "Visit: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
echo ""
read -p "Press Enter after enabling billing..."

# Enable APIs
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Set region
gcloud config set run/region $REGION

# Build and deploy using Cloud Build (this avoids ECR issues)
echo "Building and deploying with Cloud Build..."

# Create a simple cloudbuild.yaml
cat > cloudbuild.yaml << 'EOF'
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-f', 'Dockerfile.prod', '-t', 'gcr.io/$PROJECT_ID/wordbattle-backend', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/wordbattle-backend']
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'wordbattle-backend'
      - '--image=gcr.io/$PROJECT_ID/wordbattle-backend'
      - '--region=europe-west1'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--port=8000'
      - '--memory=512Mi'
      - '--set-env-vars=DB_HOST=wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com,DB_NAME=wordbattle,DB_USER=postgres,DB_PASSWORD=Wordbattle2024'
EOF

# Submit build
echo "Submitting build to Google Cloud Build..."
gcloud builds submit --config cloudbuild.yaml .

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment successful!"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
    
    echo ""
    echo "🚀 Your application is now live!"
    echo "================================"
    echo "Application URL: $SERVICE_URL"
    echo "Health check: $SERVICE_URL/health"
    echo "Debug tokens: $SERVICE_URL/debug/tokens"
    echo ""
    echo "Testing endpoints..."
    
    # Wait a moment for service to be ready
    sleep 15
    
    # Test health
    echo "Testing health endpoint..."
    curl -s "$SERVICE_URL/health" | jq . || echo "Health endpoint response: $(curl -s $SERVICE_URL/health)"
    
    echo ""
    echo "Testing debug tokens..."
    curl -s "$SERVICE_URL/debug/tokens" | jq . || echo "Debug tokens response: $(curl -s $SERVICE_URL/debug/tokens)"
    
    echo ""
    echo "✅ Google Cloud Run deployment complete!"
    echo "Your WordBattle backend is now running outside AWS!"
    echo ""
    echo "Next steps:"
    echo "1. Update your frontend to use: $SERVICE_URL"
    echo "2. Test the invitation functionality with the new emails"
    echo "3. Clean up AWS App Runner resources"
    
else
    echo "❌ Deployment failed"
    echo "Check the Cloud Build logs in the Google Cloud Console"
fi

# Clean up
rm -f cloudbuild.yaml 