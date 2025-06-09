#!/bin/bash

# Production deployment script for WordBattle Backend
# This script deploys to Google Cloud Run with production configuration

set -e

echo "🚀 Deploying WordBattle Backend to Production..."

# Configuration
SERVICE_NAME="wordbattle-backend-prod"
REGION="europe-west1"
PROJECT_ID="wordbattle-1748668162"
MEMORY="1Gi"
CPU="1"
TIMEOUT="300"
CONCURRENCY="100"
MIN_INSTANCES="0"
MAX_INSTANCES="10"

# Check if we're deploying from a clean git state
if ! git diff --quiet || ! git diff --staged --quiet; then
    echo "⚠️  WARNING: You have uncommitted changes!"
    echo "Please commit and push your changes before deploying to production."
    echo "Current status:"
    git status --short
    echo ""
    echo "To deploy anyway (NOT RECOMMENDED), use: ./deploy-production.sh --force"
    if [[ "$1" != "--force" ]]; then
        exit 1
    fi
    echo "🚨 DEPLOYING WITH UNCOMMITTED CHANGES (as requested with --force)"
fi

# Check if we're up to date with remote
if git status --porcelain -b | grep -q 'ahead\|behind'; then
    echo "⚠️  WARNING: Your branch is not in sync with origin!"
    echo "Please push your commits or pull remote changes first."
    echo "Current status:"
    git status
    echo ""
    echo "To deploy anyway (NOT RECOMMENDED), use: ./deploy-production.sh --force"
    if [[ "$1" != "--force" ]]; then
        exit 1
    fi
    echo "🚨 DEPLOYING OUT OF SYNC WITH REMOTE (as requested with --force)"
fi

# Get current commit for deployment tagging
COMMIT_HASH=$(git rev-parse --short HEAD)
COMMIT_MESSAGE=$(git log -1 --pretty=format:"%s")
DEPLOY_TAG="deploy-prod-$(date +%Y%m%d-%H%M%S)"

echo "📋 Deployment Info:"
echo "   🏷️  Tag: $DEPLOY_TAG" 
echo "   🔗 Commit: $COMMIT_HASH"
echo "   📝 Message: $COMMIT_MESSAGE"
echo ""

# Generate a secure SECRET_KEY
echo "🔐 Generating secure SECRET_KEY..."
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
echo "✅ SECRET_KEY generated: ${SECRET_KEY:0:20}..."

# Tag the deployment
git tag -a "$DEPLOY_TAG" -m "Production deployment: $COMMIT_MESSAGE"

# Set production environment variables
echo "📦 Building and deploying service..."

# Deploy to Cloud Run from git repository
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
  --set-env-vars="ENVIRONMENT=production" \
  --set-env-vars="SECRET_KEY=$SECRET_KEY" \
  --set-env-vars="SMTP_SERVER=smtp.strato.de" \
  --set-env-vars="SMTP_PORT=465" \
  --set-env-vars="SMTP_USE_SSL=true" \
  --set-env-vars="SMTP_USERNAME=jan@binge-dev.de" \
  --set-env-vars="SMTP_PASSWORD=q2NvW4J1%tcAyJSg8" \
  --set-env-vars="FROM_EMAIL=jan@binge-dev.de" \
  --set-env-vars="CORS_ORIGINS=*" \
  --add-cloudsql-instances="wordbattle-1748668162:europe-west1:wordbattle-db" \
  --set-env-vars="DATABASE_URL=postgresql://postgres:8G9kH2mP4vN1qR7sT6eW@/wordbattle_db?host=/cloudsql/wordbattle-1748668162:europe-west1:wordbattle-db" \
  --execution-environment gen2

echo "✅ Production deployment completed!"

# Push the deployment tag
echo "🏷️  Pushing deployment tag to remote..."
git push origin "$DEPLOY_TAG"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "🌐 Service URL: $SERVICE_URL"

echo "🧪 Testing deployment..."

# Wait a moment for service to be ready
sleep 10

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
    echo "❌ Health endpoint test failed"
    echo "Response:"
    curl -s "$SERVICE_URL/health" || echo "No response"
fi

# Test admin endpoints
echo "Testing admin endpoint..."
if curl -f -s "$SERVICE_URL/admin/database/wordlist-status" > /dev/null; then
    echo "✅ Admin endpoint test passed"
else
    echo "⚠️  Admin endpoint test failed (expected - may need database setup)"
    echo "Response:"
    curl -s "$SERVICE_URL/admin/database/wordlist-status" || echo "No response"
fi

echo "🎉 Production deployment successful!"
echo ""
echo "📋 IMPORTANT - Save this information:"
echo "   🔑 SECRET_KEY: $SECRET_KEY"
echo "   🌐 Production URL: $SERVICE_URL"
echo ""
echo "📋 Next steps:"
echo "   1. Set admin flag in database: UPDATE users SET is_admin = true WHERE email = 'your@email.com';"
echo "   2. Import wordlists: curl -X POST '$SERVICE_URL/admin/database/import-wordlists'"
echo "   3. Verify admin endpoints: curl '$SERVICE_URL/admin/database/wordlist-status'"
echo "   4. Documentation: $SERVICE_URL/docs"
echo ""
echo "🔧 Environment setup complete!" 