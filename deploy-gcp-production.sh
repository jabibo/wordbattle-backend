#!/bin/bash

# WordBattle Backend - Google Cloud Run Multi-Environment Deployment (Bash)

# Default values
ENVIRONMENT="production"
GIT_BRANCH=""
SKIP_GIT_CHECK=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -b|--branch)
            GIT_BRANCH="$2"
            shift 2
            ;;
        --skip-git-check)
            SKIP_GIT_CHECK=true
            shift
            ;;
        production)
            ENVIRONMENT="production"
            shift
            ;;
        testing)
            ENVIRONMENT="testing"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS] [ENVIRONMENT]"
            echo ""
            echo "Options:"
            echo "  -e, --environment ENV    Set environment (production|testing)"
            echo "  -b, --branch BRANCH      Git branch to deploy"
            echo "  --skip-git-check         Skip Git integration checks"
            echo "  -h, --help               Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 production            Deploy to production"
            echo "  $0 testing               Deploy to testing"
            echo "  $0 -e production -b main Deploy main branch to production"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "production" && "$ENVIRONMENT" != "testing" ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "Must be 'production' or 'testing'"
    exit 1
fi

echo "🚀 WordBattle Backend - Google Cloud Run Deployment"
echo "================================================="
echo "Deploying to environment: $ENVIRONMENT"
echo ""

# Configuration
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
        if ! git checkout "$GIT_BRANCH"; then
            echo "❌ Failed to switch to branch: $GIT_BRANCH"
            exit 1
        fi
    fi
    
    # Check for uncommitted changes
    if [[ -n $(git status --porcelain) ]]; then
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
    if ! git pull origin "$GIT_BRANCH"; then
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
    IMAGE_TAG=${GIT_COMMIT:+prod-$GIT_COMMIT}
    IMAGE_TAG=${IMAGE_TAG:-prod-latest}
    MIN_INSTANCES=1
    MAX_INSTANCES=100
    MEMORY="2Gi"
    CPU="2"
else
    SERVICE_NAME="$BASE_SERVICE_NAME-test"
    IMAGE_TAG=${GIT_COMMIT:+test-$GIT_COMMIT}
    IMAGE_TAG=${IMAGE_TAG:-test-latest}
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
if ! command -v gcloud >/dev/null 2>&1; then
    echo "❌ Google Cloud CLI not found."
    echo "Please install it first: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo "✅ Google Cloud CLI found"

# Check if Docker is installed
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker not found."
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✅ Docker found"

# Wait for Docker to start
echo "Waiting for Docker to start..."
DOCKER_READY=false
for i in {1..30}; do
    if docker ps >/dev/null 2>&1; then
        echo "✅ Docker is running"
        DOCKER_READY=true
        break
    fi
    sleep 1
done

if [[ "$DOCKER_READY" != "true" ]]; then
    echo "❌ Docker failed to start after 30 seconds"
    echo "Please start Docker manually and try again"
    exit 1
fi

# Check if logged in to gcloud
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [[ -z "$ACTIVE_ACCOUNT" ]]; then
    echo "Please login to Google Cloud:"
    gcloud auth login
fi

echo "✅ Prerequisites check passed"
echo ""

# Set project and region
echo "Setting project and region..."
gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"

# Configure Docker for GCR
echo "Configuring Docker for Google Container Registry..."
gcloud auth configure-docker --quiet

echo "✅ Configuration complete"
echo ""

# Build Docker image
echo "Building Docker image for $ENVIRONMENT environment..."
TIMESTAMP=$(date +%s)

# Build arguments for environment variables
BUILD_ARGS=(
    --build-arg "ENVIRONMENT=$ENVIRONMENT"
)

if [[ -n "$GIT_COMMIT" ]]; then
    BUILD_ARGS+=(
        --build-arg "GIT_COMMIT=$GIT_COMMIT"
        --build-arg "GIT_BRANCH=$GIT_BRANCH"
        --build-arg "DEPLOY_TIMESTAMP=$TIMESTAMP"
    )
fi

# Build the image
if ! docker build "${BUILD_ARGS[@]}" \
    -t "gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG" \
    -t "gcr.io/$PROJECT_ID/$IMAGE_NAME:latest" .; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully"

# Push image to GCR
echo "Pushing image to Google Container Registry..."
if ! docker push "gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG"; then
    echo "❌ Failed to push image to GCR"
    exit 1
fi

if ! docker push "gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"; then
    echo "❌ Failed to push latest tag to GCR"
    exit 1
fi

echo "✅ Image pushed to GCR successfully"
echo ""

# Deploy to Cloud Run
echo "Deploying to Google Cloud Run ($ENVIRONMENT environment)..."

# Create environment variables for the service
ENV_VARS=(
    "ENVIRONMENT=$ENVIRONMENT"
)

if [[ -n "$GIT_COMMIT" ]]; then
    ENV_VARS+=(
        "GIT_COMMIT=$GIT_COMMIT"
        "GIT_BRANCH=$GIT_BRANCH"
        "DEPLOY_TIMESTAMP=$TIMESTAMP"
    )
fi

# Deploy the service
if ! gcloud run deploy "$SERVICE_NAME" \
    --image="gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --memory="$MEMORY" \
    --cpu="$CPU" \
    --min-instances="$MIN_INSTANCES" \
    --max-instances="$MAX_INSTANCES" \
    --set-env-vars="$(IFS=,; echo "${ENV_VARS[*]}")" \
    --port=8000 \
    --timeout=300; then
    echo "❌ Deployment failed"
    exit 1
fi

echo "✅ Deployment successful!"

# Create Git tag for production deployments
if [[ "$ENVIRONMENT" == "production" && "$SKIP_GIT_CHECK" != "true" ]]; then
    DEPLOY_TAG="deploy-prod-$(date +%Y%m%d-%H%M%S)"
    echo "Creating Git tag: $DEPLOY_TAG"
    if git tag "$DEPLOY_TAG" && git push origin "$DEPLOY_TAG"; then
        echo "✅ Git tag created and pushed"
    else
        echo "⚠️  Failed to create Git tag (deployment still successful)"
    fi
fi

echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")

echo "🎉 Deployment completed successfully!"
echo ""
echo "Service URLs:"
echo "  Application: $SERVICE_URL"
echo "  API Docs: $SERVICE_URL/docs"
echo "  Health Check: $SERVICE_URL/health"
echo ""

# Test deployment
echo "Testing deployment..."
echo "Testing health endpoint..."
if curl -f -s "$SERVICE_URL/health" >/dev/null; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check failed (service might still be starting)"
fi

echo "Testing API documentation..."
if curl -f -s "$SERVICE_URL/docs" >/dev/null; then
    echo "✅ API documentation accessible!"
else
    echo "⚠️  API documentation not accessible"
fi

echo ""
echo "🚀 Deployment to $ENVIRONMENT environment complete!"
echo "Service is available at: $SERVICE_URL" 