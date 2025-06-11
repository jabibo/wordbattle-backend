#!/bin/bash

# WordBattle Backend - Google Cloud Run Multi-Environment Deployment
# Usage: ./deploy-gcp-production.sh [production|testing] [git-branch] [--skip-git-check]

ENVIRONMENT=${1:-production}
GIT_BRANCH=${2:-""}
SKIP_GIT_CHECK=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --skip-git-check)
            SKIP_GIT_CHECK=true
            shift
            ;;
    esac
done

echo "🚀 WordBattle Backend - Google Cloud Run Deployment"
echo "================================================="
echo "Deploying to environment: $ENVIRONMENT"
echo ""

# Validate environment
if [[ "$ENVIRONMENT" != "production" && "$ENVIRONMENT" != "testing" ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "Valid options: production, testing"
    exit 1
fi

# Configuration based on environment
PROJECT_ID="wordbattle-1748668162"
BASE_SERVICE_NAME="wordbattle-backend"
REGION="europe-west1"
IMAGE_NAME="wordbattle-backend"

# Git integration
if [[ "$SKIP_GIT_CHECK" != "true" ]]; then
    echo "🔍 Git Integration Check..."
    
    # Check if we're in a git repository
    if ! git status >/dev/null 2>&1; then
        echo "❌ Not in a Git repository or Git not installed"
        echo "Please run from the project root or use --skip-git-check"
        exit 1
    fi
    
    # Get current branch
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
    if [[ -z "$GIT_BRANCH" ]]; then
        GIT_BRANCH="$CURRENT_BRANCH"
    fi
    
    echo "  Current branch: $CURRENT_BRANCH"
    echo "  Target branch: $GIT_BRANCH"
    
    # Switch to target branch if different
    if [[ "$CURRENT_BRANCH" != "$GIT_BRANCH" ]]; then
        echo "  Switching to branch: $GIT_BRANCH"
        git checkout "$GIT_BRANCH"
        if [[ $? -ne 0 ]]; then
            echo "❌ Failed to switch to branch: $GIT_BRANCH"
            exit 1
        fi
    fi
    
    # Check for uncommitted changes
    GIT_STATUS=$(git status --porcelain)
    if [[ -n "$GIT_STATUS" ]]; then
        echo "⚠️  Uncommitted changes detected:"
        git status --short
        if [[ "$ENVIRONMENT" == "production" ]]; then
            echo "❌ Production deployments require clean working directory"
            echo "Please commit or stash your changes before deploying to production"
            exit 1
        else
            echo "🧪 Testing environment allows uncommitted changes"
        fi
    else
        echo "✅ Working directory is clean"
    fi
    
    # Pull latest changes
    echo "  Pulling latest changes from origin/$GIT_BRANCH..."
    git pull origin "$GIT_BRANCH"
    if [[ $? -ne 0 ]]; then
        echo "⚠️  Failed to pull latest changes (continuing anyway)"
    fi
    
    # Get commit information
    GIT_COMMIT=$(git rev-parse --short HEAD)
    GIT_COMMIT_FULL=$(git rev-parse HEAD)
    GIT_COMMIT_MESSAGE=$(git log -1 --pretty=format:"%s")
    GIT_COMMIT_AUTHOR=$(git log -1 --pretty=format:"%an")
    GIT_COMMIT_DATE=$(git log -1 --pretty=format:"%cd" --date=iso)
    
    echo "  Commit: $GIT_COMMIT"
    echo "  Message: $GIT_COMMIT_MESSAGE"
    echo "  Author: $GIT_COMMIT_AUTHOR"
    echo "  Date: $GIT_COMMIT_DATE"
    
    echo "✅ Git integration check passed"
    echo ""
fi

# Environment-specific configuration
if [[ "$ENVIRONMENT" == "production" ]]; then
    SERVICE_NAME="$BASE_SERVICE_NAME-prod"
    IMAGE_TAG=${GIT_COMMIT:+"prod-$GIT_COMMIT"}
    IMAGE_TAG=${IMAGE_TAG:-"prod-latest"}
    MIN_INSTANCES=1
    MAX_INSTANCES=100
    MEMORY="2Gi"
    CPU="2"
else
    SERVICE_NAME="$BASE_SERVICE_NAME-test"
    IMAGE_TAG=${GIT_COMMIT:+"test-$GIT_COMMIT"}
    IMAGE_TAG=${IMAGE_TAG:-"test-latest"}
    MIN_INSTANCES=0
    MAX_INSTANCES=10
    MEMORY="1Gi"
    CPU="1"
fi

echo "Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Environment: $ENVIRONMENT"
echo "  Service: $SERVICE_NAME"
echo "  Region: $REGION"
echo "  Image: $IMAGE_NAME:$IMAGE_TAG"
echo "  Resources: $CPU CPU, $MEMORY RAM"
echo "  Scaling: $MIN_INSTANCES-$MAX_INSTANCES instances"
if [[ -n "$GIT_COMMIT" ]]; then
    echo "  Git Commit: $GIT_COMMIT ($GIT_BRANCH)"
fi
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI not found."
    echo "Please install it first:"
    echo "Windows: winget install --id Google.CloudSDK"
    echo "Linux/Mac: curl https://sdk.cloud.google.com | bash"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found."
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Wait for Docker to start
echo "Waiting for Docker to start..."
for i in {1..30}; do
    if docker ps >/dev/null 2>&1; then
        echo "✅ Docker is running"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Docker failed to start after 30 seconds"
        echo "Please start Docker manually and try again"
        exit 1
    fi
    sleep 1
done

# Check if logged in to gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Please login to Google Cloud:"
    gcloud auth login
fi

echo "✅ Prerequisites check passed"
echo ""

# Set project and region
echo "Setting project and region..."
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

if [ $? -ne 0 ]; then
    echo "❌ Failed to set project. Please make sure project $PROJECT_ID exists and you have access."
    exit 1
fi

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com

echo "✅ Google Cloud setup complete"
echo ""

# Build the Docker image
echo "Building Docker image for $ENVIRONMENT environment..."
if [[ -n "$GIT_COMMIT" ]]; then
    echo "  Including Git commit: $GIT_COMMIT"
fi

DOCKER_BUILD_ARGS=""
if [[ -n "$GIT_COMMIT" ]]; then
    DOCKER_BUILD_ARGS="--label git.commit=$GIT_COMMIT_FULL"
    DOCKER_BUILD_ARGS="$DOCKER_BUILD_ARGS --label git.branch=$GIT_BRANCH"
    DOCKER_BUILD_ARGS="$DOCKER_BUILD_ARGS --label git.message='$GIT_COMMIT_MESSAGE'"
    DOCKER_BUILD_ARGS="$DOCKER_BUILD_ARGS --label deploy.environment=$ENVIRONMENT"
    DOCKER_BUILD_ARGS="$DOCKER_BUILD_ARGS --label deploy.timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
fi

DOCKER_BUILDKIT=0 docker build $DOCKER_BUILD_ARGS -f Dockerfile.cloudrun -t gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully"
echo ""

# Configure Docker to use gcloud as a credential helper
echo "Configuring Docker for Google Container Registry..."
gcloud auth configure-docker --quiet

# Push the image to Google Container Registry
echo "Pushing image to Google Container Registry..."
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG

if [ $? -ne 0 ]; then
    echo "❌ Docker push failed"
    exit 1
fi

echo "✅ Image pushed to GCR successfully"
echo ""

# Deploy to Cloud Run
echo "Deploying to Google Cloud Run ($ENVIRONMENT environment)..."

# First check if we need to create or update the service
if gcloud run services describe $SERVICE_NAME --region=$REGION >/dev/null 2>&1; then
    echo "Updating existing Cloud Run service: $SERVICE_NAME"
else
    echo "Creating new Cloud Run service: $SERVICE_NAME"
fi

# Environment-specific environment variables
ENV_VARS=""
if [[ "$ENVIRONMENT" == "production" ]]; then
    ENV_VARS="ENVIRONMENT=production,LOG_LEVEL=INFO,DEBUG=false"
else
    ENV_VARS="ENVIRONMENT=testing,LOG_LEVEL=DEBUG,DEBUG=true"
    ENV_VARS="$ENV_VARS,DATABASE_URL=postgresql://wordbattle:wordbattle123@/wordbattle_test?host=/cloudsql/wordbattle-1748668162:europe-west1:wordbattle-db"
fi

# Add Git information to environment variables
if [[ -n "$GIT_COMMIT" ]]; then
    ENV_VARS="$ENV_VARS,GIT_COMMIT=$GIT_COMMIT,GIT_BRANCH=$GIT_BRANCH,DEPLOY_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
fi

# Build gcloud run deploy command
DEPLOY_ARGS=(
    "run" "deploy" "$SERVICE_NAME"
    "--image=gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG"
    "--platform=managed"
    "--region=$REGION"
    "--allow-unauthenticated"
    "--port=8000"
    "--memory=$MEMORY"
    "--cpu=$CPU"
    "--timeout=300"
    "--max-instances=$MAX_INSTANCES"
    "--min-instances=$MIN_INSTANCES"
    "--concurrency=80"
    "--set-env-vars=$ENV_VARS"
)

# Add Cloud SQL connection for testing environment
if [[ "$ENVIRONMENT" == "testing" ]]; then
    DEPLOY_ARGS+=("--add-cloudsql-instances=wordbattle-1748668162:europe-west1:wordbattle-db")
fi

gcloud "${DEPLOY_ARGS[@]}"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment successful!"
    
    # Create Git tag for production deployments
    if [[ "$ENVIRONMENT" == "production" && -n "$GIT_COMMIT" && "$SKIP_GIT_CHECK" != "true" ]]; then
        DEPLOY_TAG="deploy-prod-$(date +%Y%m%d-%H%M%S)"
        echo "Creating Git tag: $DEPLOY_TAG"
        git tag -a "$DEPLOY_TAG" -m "Production deployment at $(date '+%Y-%m-%d %H:%M:%S')"
        git push origin "$DEPLOY_TAG"
        echo "✅ Git tag created and pushed"
    fi
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
    
    echo ""
    echo "🚀 WordBattle Backend ($ENVIRONMENT) is now live!"
    echo "================================================"
    echo "Application URL: $SERVICE_URL"
    echo "API Documentation: $SERVICE_URL/docs"
    echo "Health Check: $SERVICE_URL/health"
    echo "Database Status: $SERVICE_URL/database/status"
    echo ""
    
    echo "Testing deployment..."
    sleep 10
    
    # Test health endpoint
    echo "Testing health endpoint..."
    HEALTH_RESPONSE=$(curl -s -w "%{http_code}" "$SERVICE_URL/health")
    HTTP_STATUS="${HEALTH_RESPONSE: -3}"
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "✅ Health check passed!"
    else
        echo "⚠️  Health check returned status: $HTTP_STATUS"
    fi
    
    # Test API documentation
    echo "Testing API documentation..."
    DOCS_RESPONSE=$(curl -s -w "%{http_code}" "$SERVICE_URL/docs")
    DOCS_STATUS="${DOCS_RESPONSE: -3}"
    
    if [ "$DOCS_STATUS" = "200" ]; then
        echo "✅ API documentation accessible!"
    else
        echo "⚠️  API docs returned status: $DOCS_STATUS"
    fi
    
    echo ""
    echo "🎉 Google Cloud Run deployment complete!"
    echo ""
    echo "📋 Deployment Summary:"
    echo "  ✅ Environment: $ENVIRONMENT"
    if [[ -n "$GIT_COMMIT" ]]; then
        echo "  ✅ Git Commit: $GIT_COMMIT ($GIT_BRANCH)"
        if [[ "$ENVIRONMENT" == "production" ]]; then
            echo "  ✅ Git tag created: $DEPLOY_TAG"
        fi
    fi
    echo "  ✅ Docker image built and pushed to GCR"
    echo "  ✅ Cloud Run service deployed: $SERVICE_NAME"
    echo "  ✅ Service is publicly accessible"
    echo "  ✅ Health checks passing"
    echo ""
    echo "🔗 Important URLs:"
    echo "  Application: $SERVICE_URL"
    echo "  API Docs: $SERVICE_URL/docs"
    echo "  OpenAPI Schema: $SERVICE_URL/openapi.json"
    echo ""
    echo "🎯 Environment-Specific Info:"
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo "  🏭 Production Environment"
        echo "  • Always-on with minimum 1 instance"
        echo "  • High performance: 2 CPU, 2GB RAM"
        echo "  • Scales up to 100 instances"
        echo "  • Optimized for stability and performance"
        echo "  • Git tags created for tracking deployments"
    else
        echo "  🧪 Testing Environment"
        echo "  • Cost-optimized: scales to 0 when idle"
        echo "  • Basic performance: 1 CPU, 1GB RAM"
        echo "  • Scales up to 10 instances"
        echo "  • Debug mode enabled for development"
        echo "  • Allows uncommitted changes for testing"
    fi
    echo ""
    echo "📝 Project Details:"
    echo "  Project ID: $PROJECT_ID"
    echo "  Service Name: $SERVICE_NAME"
    echo "  Region: $REGION"
    echo "  Image: gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG"
    
    # Show both environment URLs if this is production
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo ""
        echo "🔄 Environment Management:"
        echo "  Production: $SERVICE_URL"
        
        # Check if testing environment exists
        if gcloud run services describe "$BASE_SERVICE_NAME-test" --region=$REGION >/dev/null 2>&1; then
            TEST_URL=$(gcloud run services describe "$BASE_SERVICE_NAME-test" --region=$REGION --format='value(status.url)')
            echo "  Testing: $TEST_URL"
        else
            echo "  Testing: Not deployed (run: ./deploy-gcp-production.sh testing)"
        fi
        
        echo ""
        echo "🏷️  Git Management:"
        echo "  Deploy to testing: ./deploy-gcp-production.sh testing"
        echo "  Deploy specific branch: ./deploy-gcp-production.sh production feature/xyz"
        echo "  Skip Git checks: ./deploy-gcp-production.sh production '' --skip-git-check"
    fi
    
else
    echo "❌ Deployment failed"
    echo "Check the logs with: gcloud run services logs tail $SERVICE_NAME --region=$REGION"
    exit 1
fi 