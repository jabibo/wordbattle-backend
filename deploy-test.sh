#!/bin/bash

# Test deployment script for WordBattle Backend
# This script deploys to Google Cloud Run test environment

set -e

echo "🧪 Deploying WordBattle Backend to Test Environment..."

# Configuration
SERVICE_NAME="wordbattle-backend-test"
REGION="europe-west1"
PROJECT_ID="wordbattle-1748668162"
MEMORY="1Gi"
CPU="1"
TIMEOUT="300"
CONCURRENCY="100"
MIN_INSTANCES="0"
MAX_INSTANCES="10"

# Generate a secure SECRET_KEY for test
echo "🔐 Generating secure SECRET_KEY for test..."
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
echo "✅ SECRET_KEY generated: ${SECRET_KEY:0:20}..."

# Deploy to Cloud Run (test environment)
echo "📦 Building and deploying test service..."

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory $MEMORY \
  --cpu $CPU \
  --timeout $TIMEOUT \
  --concurrency $CONCURRENCY \
  --min-instances $MIN_INSTANCES \
  --max-instances $MAX_INSTANCES \
  --set-env-vars="SECRET_KEY=$SECRET_KEY" \
  --set-env-vars="ENVIRONMENT=test" \
  --set-env-vars="SMTP_SERVER=smtp.strato.de" \
  --set-env-vars="SMTP_PORT=465" \
  --set-env-vars="SMTP_USE_SSL=true" \
  --set-env-vars="SMTP_USERNAME=jan@binge-dev.de" \
  --set-env-vars="SMTP_PASSWORD=q2NvW4J1%tcAyJSg8" \
  --set-env-vars="FROM_EMAIL=jan@binge-dev.de" \
  --set-env-vars="CORS_ORIGINS=*" \
  --execution-environment gen2

echo "✅ Test deployment completed!"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "🌐 Service URL: $SERVICE_URL"

echo "🧪 Testing deployment..."

# Wait a moment for service to be ready
sleep 5

# Test basic endpoint
echo "Testing basic endpoint..."
if curl -f -s "$SERVICE_URL/" > /dev/null; then
    echo "✅ Basic endpoint test passed"
else
    echo "❌ Basic endpoint test failed"
    echo "Response:"
    curl -s "$SERVICE_URL/" || echo "No response"
    exit 1
fi

# Test health endpoint
echo "Testing health endpoint..."
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo "✅ Health endpoint test passed"
else
    echo "⚠️  Health endpoint test failed"
    echo "Response:"
    curl -s "$SERVICE_URL/health" || echo "No response"
fi

echo "🎉 Test deployment successful!"
echo ""
echo "📋 Test Environment Info:"
echo "   🔑 SECRET_KEY: $SECRET_KEY"
echo "   🌐 Test URL: $SERVICE_URL"
echo "   📚 Documentation: $SERVICE_URL/docs"
echo "   🐛 Debug tokens: $SERVICE_URL/debug/tokens"
echo ""
echo "🔧 Test environment ready for development!" 