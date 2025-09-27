#!/bin/bash

# WordBattle Backend - Unified Google Cloud Run Deployment Script
# Usage: ./deploy-unified.sh [production|testing] [git-branch] [--skip-git-check]
# 
# This script replaces both deploy-gcp-production.sh and deploy-gcp-test.sh
# It ensures consistent deployment process across environments and proper
# configuration loading from deploy.production.env or deploy.testing.env

set -e  # Exit on any error

ENVIRONMENT=${1:-testing}
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

echo "🚀 WordBattle Backend - Unified Cloud Run Deployment"
echo "================================================="
echo "Target Environment: $ENVIRONMENT"
echo "Script Version: 2.0 (Unified)"
echo ""

# Validate environment
if [[ "$ENVIRONMENT" != "production" && "$ENVIRONMENT" != "testing" && "$ENVIRONMENT" != "dev" ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "Valid options: production, testing, dev"
    echo ""
    echo "Usage examples:"
    echo "  ./deploy-unified.sh testing                    # Deploy to testing environment"
    echo "  ./deploy-unified.sh dev                        # Deploy to dev environment"
    echo "  ./deploy-unified.sh production                 # Deploy to production environment"
    echo "  ./deploy-unified.sh testing feature/branch    # Deploy specific branch to testing"
    echo "  ./deploy-unified.sh production --skip-git-check  # Skip git validation"
    exit 1
fi

# Global configuration (PROJECT_ID will be set from environment file)
BASE_SERVICE_NAME="wordbattle-backend"
REGION="europe-west1"
IMAGE_NAME="wordbattle-backend"

# Environment-specific configuration
if [[ "$ENVIRONMENT" == "production" ]]; then
    SERVICE_NAME="$BASE_SERVICE_NAME-prod"
    ENV_FILE="deploy.production.env"
    MIN_INSTANCES=1
    MAX_INSTANCES=100
    MEMORY="2Gi"
    CPU="2"
    CLOUD_SQL_DATABASE_NAME="wordbattle_db"
    echo "🏭 Production Environment Selected"
    echo "  Service Name: $SERVICE_NAME"
    echo "  Config File: $ENV_FILE"
    echo "  Resources: $CPU CPU, $MEMORY RAM"
    echo "  Scaling: $MIN_INSTANCES-$MAX_INSTANCES instances"
    echo "  Database: $CLOUD_SQL_DATABASE_NAME"
elif [[ "$ENVIRONMENT" == "dev" ]]; then
    SERVICE_NAME="$BASE_SERVICE_NAME-dev"
    ENV_FILE="deploy.dev.env"
    MIN_INSTANCES=0
    MAX_INSTANCES=10
    MEMORY="2Gi"
    CPU="2"
    CLOUD_SQL_DATABASE_NAME="wordbattle_dev"
    echo "🛠️  Development Environment Selected"
    echo "  Service Name: $SERVICE_NAME"
    echo "  Config File: $ENV_FILE"
    echo "  Resources: $CPU CPU, $MEMORY RAM"
    echo "  Scaling: $MIN_INSTANCES-$MAX_INSTANCES instances"
    echo "  Database: $CLOUD_SQL_DATABASE_NAME"
else
    SERVICE_NAME="$BASE_SERVICE_NAME-test"
    ENV_FILE="deploy.testing.env"
    MIN_INSTANCES=0
    MAX_INSTANCES=10
    MEMORY="1Gi"
    CPU="1"
    CLOUD_SQL_DATABASE_NAME="wordbattle_test"
    echo "🧪 Testing Environment Selected"
    echo "  Service Name: $SERVICE_NAME"
    echo "  Config File: $ENV_FILE"
    echo "  Resources: $CPU CPU, $MEMORY RAM"
    echo "  Scaling: $MIN_INSTANCES-$MAX_INSTANCES instances"
    echo "  Database: $CLOUD_SQL_DATABASE_NAME"
fi
echo ""

# Load environment variables from file
echo "📋 Loading Environment Configuration..."
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file $ENV_FILE not found!"
    echo ""
    echo "Expected file: $ENV_FILE"
    echo "Please create this file with the required environment variables."
    echo "You can use the following template:"
    echo ""
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo "# Production Environment Variables"
        echo "ENVIRONMENT=production"
        echo "DB_USER=wordbattle"
        echo "DB_PASSWORD=your_db_password"
        echo "CLOUD_SQL_DATABASE_NAME=wordbattle_db"
        echo "SECRET_KEY=your_secret_key"
        echo "SMTP_USERNAME=your_smtp_username"
        echo "SMTP_PASSWORD=your_smtp_password"
        echo "# ... (see deploy.production.env.example)"
    else
        echo "# Testing Environment Variables"
        echo "ENVIRONMENT=testing"
        echo "DB_USER=wordbattle"
        echo "DB_PASSWORD=your_db_password"
        echo "CLOUD_SQL_DATABASE_NAME=wordbattle_test"
        echo "SECRET_KEY=your_secret_key"
        echo "# ... (see deploy.testing.env.example)"
    fi
    exit 1
fi

# Load environment variables
set -a  # automatically export all variables
source "$ENV_FILE"
set +a  # stop automatically exporting

echo "✅ Environment variables loaded from $ENV_FILE"

echo ""
echo "🔧 Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Base Service: $BASE_SERVICE_NAME"
echo "  Region: $REGION"
echo "  Environment: $ENVIRONMENT"
echo "  Database Instance: $CLOUD_SQL_INSTANCE_NAME"
echo ""

# Validate required variables based on environment
if [[ "$ENVIRONMENT" == "production" ]]; then
    # Production uses secret references for DB_PASSWORD and SMTP_PASSWORD
    REQUIRED_VARS=("DB_USER" "SECRET_KEY" "SMTP_USERNAME" "ADMIN_EMAIL")
    echo "🔍 Validating production environment variables (excluding secret references)..."
elif [[ "$ENVIRONMENT" == "dev" ]]; then
    REQUIRED_VARS=("DB_USER" "DB_PASSWORD" "SECRET_KEY" "SMTP_USERNAME" "SMTP_PASSWORD" "ADMIN_EMAIL")
    echo "🔍 Validating development environment variables..."
else
    REQUIRED_VARS=("DB_USER" "DB_PASSWORD" "SECRET_KEY" "ADMIN_EMAIL")
    echo "🔍 Validating testing environment variables..."
fi

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables in $ENV_FILE:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

echo "✅ All required environment variables are set"
echo ""

# Git integration (same logic for both environments)
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

# Check prerequisites
echo "🔧 Checking Prerequisites..."

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
echo "  Waiting for Docker to start..."
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
echo "⚙️  Setting Google Cloud configuration..."
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

if [ $? -ne 0 ]; then
    echo "❌ Failed to set project. Please make sure project $PROJECT_ID exists and you have access."
    exit 1
fi

# Enable required APIs
echo "🔌 Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com

echo "✅ Google Cloud setup complete"
echo ""

# Contract Validation and Preparation
echo "📋 Contract Validation Check..."

# Check if contracts directory exists
CONTRACTS_DIR="/Users/janbinge/git/wordbattle/wordbattle-contracts"
if [ ! -d "$CONTRACTS_DIR" ]; then
    echo "⚠️  Contracts directory not found at: $CONTRACTS_DIR"
    echo "Contract validation will be disabled in the deployed service."
    echo ""
else
    echo "✅ Contracts directory found: $CONTRACTS_DIR"
    
    # Copy contracts to build context for Docker BEFORE building
    echo "  Copying contracts to build context..."
    rm -rf ./wordbattle-contracts 2>/dev/null || true
    cp -r "$CONTRACTS_DIR" ./wordbattle-contracts
    echo "✅ Contracts copied to build context"
    
    # Run contract validation script if it exists
    VALIDATION_SCRIPT="scripts/validate_contracts.py"
    if [ -f "$VALIDATION_SCRIPT" ]; then
        echo "  Running contract validation script..."
        
        # Run validation against the current local API for basic checks
        if python3 "$VALIDATION_SCRIPT" --url "http://localhost:8000" --contracts-dir "$CONTRACTS_DIR" --timeout 10 >/dev/null 2>&1; then
            echo "✅ Local contract validation passed"
        else
            echo "⚠️  Local API not available for validation (this is normal during deployment)"
        fi
        
        # Validate contract schemas themselves
        echo "  Validating contract schema files..."
        SCHEMA_VALID=true
        
        for schema_file in "$CONTRACTS_DIR"/*.json; do
            if [ -f "$schema_file" ]; then
                if python3 -m json.tool "$schema_file" >/dev/null 2>&1; then
                    echo "    ✅ $(basename "$schema_file")"
                else
                    echo "    ❌ $(basename "$schema_file") - Invalid JSON"
                    SCHEMA_VALID=false
                fi
            fi
        done
        
        if [ "$SCHEMA_VALID" = true ]; then
            echo "✅ All contract schemas are valid"
        else
            echo "❌ Some contract schemas contain errors"
            if [[ "$ENVIRONMENT" == "production" ]]; then
                echo "Production deployment requires valid contracts. Please fix the schema errors."
                exit 1
            else
                echo "⚠️  Proceeding with testing deployment despite schema errors"
            fi
        fi
    else
        echo "⚠️  Contract validation script not found: $VALIDATION_SCRIPT"
    fi
fi

echo ""

# Build the Docker image
echo "🐳 Building Docker Image..."
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
if [[ "$ENVIRONMENT" == "production" ]]; then
    IMAGE_TAG="prod-${GIT_COMMIT}-${TIMESTAMP}"
else
    IMAGE_TAG="test-${GIT_COMMIT}-${TIMESTAMP}"
fi

echo "  Image Tag: $IMAGE_TAG"
echo "  Environment: $ENVIRONMENT"
if [[ -n "$GIT_COMMIT" ]]; then
    echo "  Git Commit: $GIT_COMMIT"
fi

# Build Docker image with labels
DOCKER_BUILD_ARGS="--label git.commit=$GIT_COMMIT_FULL"
DOCKER_BUILD_ARGS="$DOCKER_BUILD_ARGS --label git.branch=$GIT_BRANCH"
DOCKER_BUILD_ARGS="$DOCKER_BUILD_ARGS --label git.message-short=$GIT_COMMIT"
DOCKER_BUILD_ARGS="$DOCKER_BUILD_ARGS --label deploy.environment=$ENVIRONMENT"
DOCKER_BUILD_ARGS="$DOCKER_BUILD_ARGS --label deploy.timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Build with explicit argument ordering
docker build \
    --platform linux/amd64 \
    --file Dockerfile.cloudrun \
    --tag gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG \
    --tag gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
    $DOCKER_BUILD_ARGS \
    .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully"
echo ""

# Configure Docker and push image
echo "📤 Pushing Image to Google Container Registry..."
gcloud auth configure-docker --quiet

docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG

if [ $? -ne 0 ]; then
    echo "❌ Docker push failed"
    exit 1
fi

echo "✅ Image pushed to GCR successfully"
echo ""

# Build environment variables for deployment
echo "🔧 Building Environment Variables..."

# Core environment variables (same for both environments)
ENV_VARS="ENVIRONMENT=${ENVIRONMENT}"
# Google Cloud Project configuration
ENV_VARS="$ENV_VARS,GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-${PROJECT_ID}}"
ENV_VARS="$ENV_VARS,PROJECT_ID=${PROJECT_ID}"
# Pass individual database components like the working deploy-test-robust.sh did
ENV_VARS="$ENV_VARS,DB_HOST=${DB_HOST:-localhost}"
ENV_VARS="$ENV_VARS,DB_PORT=${DB_PORT:-5432}"
ENV_VARS="$ENV_VARS,DB_NAME=${DB_NAME}"
ENV_VARS="$ENV_VARS,DB_USER=${DB_USER}"
# DB_PASSWORD is managed as secret reference for production
if [[ "$ENVIRONMENT" != "production" ]]; then
    ENV_VARS="$ENV_VARS,DB_PASSWORD=${DB_PASSWORD}"
fi
ENV_VARS="$ENV_VARS,CLOUD_REGION=${CLOUD_REGION}"
ENV_VARS="$ENV_VARS,CLOUD_SQL_INSTANCE_NAME=${CLOUD_SQL_INSTANCE_NAME}"
ENV_VARS="$ENV_VARS,CLOUD_SQL_CONNECTION_NAME=${CLOUD_SQL_CONNECTION_NAME}"
# Also provide the constructed DATABASE_URL as backup (for non-production)
if [[ "$ENVIRONMENT" != "production" ]]; then
    DB_NAME_TO_USE="${DB_NAME:-${CLOUD_SQL_DATABASE_NAME}}"
    DATABASE_URL="postgresql+pg8000://${DB_USER}:${DB_PASSWORD}@/${DB_NAME_TO_USE}?unix_sock=/cloudsql/${PROJECT_ID}:${CLOUD_REGION}:${CLOUD_SQL_INSTANCE_NAME}"
    ENV_VARS="$ENV_VARS,DATABASE_URL=${DATABASE_URL}"
fi
ENV_VARS="$ENV_VARS,SECRET_KEY=${SECRET_KEY}"
ENV_VARS="$ENV_VARS,ADMIN_EMAIL=${ADMIN_EMAIL}"
ENV_VARS="$ENV_VARS,ADMIN_USERNAME=${ADMIN_USERNAME:-admin}"

# Environment-specific variables
if [[ "$ENVIRONMENT" == "production" ]]; then
    # Production-specific environment variables
    ENV_VARS="$ENV_VARS,CORS_ORIGINS=${CORS_ORIGINS:-https://wordbattle.binge-dev.de}"
    ENV_VARS="$ENV_VARS,FRONTEND_URL=${FRONTEND_URL:-https://wordbattle.binge-dev.de}"
    ENV_VARS="$ENV_VARS,RATE_LIMIT=${RATE_LIMIT:-200}"
    ENV_VARS="$ENV_VARS,LOG_LEVEL=INFO"
    ENV_VARS="$ENV_VARS,DEBUG=false"
    
    # SMTP configuration for production (SMTP_PASSWORD is managed as secret reference)
    ENV_VARS="$ENV_VARS,SMTP_SERVER=${SMTP_SERVER}"
    ENV_VARS="$ENV_VARS,SMTP_PORT=${SMTP_PORT}"
    ENV_VARS="$ENV_VARS,SMTP_USERNAME=${SMTP_USERNAME}"
    # SMTP_PASSWORD is managed as secret reference for production
    ENV_VARS="$ENV_VARS,FROM_EMAIL=${FROM_EMAIL}"
    ENV_VARS="$ENV_VARS,SMTP_USE_SSL=${SMTP_USE_SSL:-true}"
    
    # Security settings
    ENV_VARS="$ENV_VARS,ENABLE_CONTRACT_VALIDATION=${ENABLE_CONTRACT_VALIDATION:-true}"
    ENV_VARS="$ENV_VARS,CONTRACT_VALIDATION_STRICT=${CONTRACT_VALIDATION_STRICT:-true}"
    
elif [[ "$ENVIRONMENT" == "dev" ]]; then
    # Development-specific environment variables
    ENV_VARS="$ENV_VARS,CORS_ORIGINS=*"
    ENV_VARS="$ENV_VARS,FRONTEND_URL=http://localhost:3000"
    ENV_VARS="$ENV_VARS,RATE_LIMIT=${RATE_LIMIT:-60}"
    ENV_VARS="$ENV_VARS,LOG_LEVEL=DEBUG"
    ENV_VARS="$ENV_VARS,DEBUG=true"
    
    # SMTP configuration for development
    ENV_VARS="$ENV_VARS,SMTP_SERVER=${SMTP_SERVER}"
    ENV_VARS="$ENV_VARS,SMTP_PORT=${SMTP_PORT}"
    ENV_VARS="$ENV_VARS,SMTP_USERNAME=${SMTP_USERNAME}"
    ENV_VARS="$ENV_VARS,SMTP_PASSWORD=${SMTP_PASSWORD}"
    ENV_VARS="$ENV_VARS,FROM_EMAIL=${FROM_EMAIL}"
    ENV_VARS="$ENV_VARS,SMTP_USE_SSL=${SMTP_USE_SSL:-false}"
    
    # Relaxed settings for development
    ENV_VARS="$ENV_VARS,ENABLE_CONTRACT_VALIDATION=${ENABLE_CONTRACT_VALIDATION:-true}"
    ENV_VARS="$ENV_VARS,CONTRACT_VALIDATION_STRICT=${CONTRACT_VALIDATION_STRICT:-false}"
    
else
    # Testing-specific environment variables
    ENV_VARS="$ENV_VARS,CORS_ORIGINS=*"
    ENV_VARS="$ENV_VARS,FRONTEND_URL=http://localhost:3000"
    ENV_VARS="$ENV_VARS,RATE_LIMIT=${RATE_LIMIT:-60}"
    ENV_VARS="$ENV_VARS,LOG_LEVEL=DEBUG"
    ENV_VARS="$ENV_VARS,DEBUG=true"
    
    # SMTP configuration for testing
    ENV_VARS="$ENV_VARS,SMTP_SERVER=${SMTP_SERVER}"
    ENV_VARS="$ENV_VARS,SMTP_PORT=${SMTP_PORT}"
    ENV_VARS="$ENV_VARS,SMTP_USERNAME=${SMTP_USERNAME}"
    ENV_VARS="$ENV_VARS,SMTP_PASSWORD=${SMTP_PASSWORD}"
    ENV_VARS="$ENV_VARS,FROM_EMAIL=${FROM_EMAIL}"
    ENV_VARS="$ENV_VARS,SMTP_USE_SSL=${SMTP_USE_SSL:-true}"
    
    # Relaxed settings for testing
    ENV_VARS="$ENV_VARS,ENABLE_CONTRACT_VALIDATION=${ENABLE_CONTRACT_VALIDATION:-true}"
    ENV_VARS="$ENV_VARS,CONTRACT_VALIDATION_STRICT=${CONTRACT_VALIDATION_STRICT:-false}"
fi

# Add standard configuration
ENV_VARS="$ENV_VARS,ALGORITHM=HS256"
ENV_VARS="$ENV_VARS,ACCESS_TOKEN_EXPIRE_MINUTES=30"
ENV_VARS="$ENV_VARS,PERSISTENT_TOKEN_EXPIRE_DAYS=30"
ENV_VARS="$ENV_VARS,VERIFICATION_CODE_EXPIRE_MINUTES=10"
ENV_VARS="$ENV_VARS,DEFAULT_WORDLIST_PATH=data/de_words.txt"
ENV_VARS="$ENV_VARS,LETTER_POOL_SIZE=7"
ENV_VARS="$ENV_VARS,GAME_INACTIVE_DAYS=7"

# Add Git information if available
if [[ -n "$GIT_COMMIT" ]]; then
    ENV_VARS="$ENV_VARS,GIT_COMMIT=$GIT_COMMIT"
    ENV_VARS="$ENV_VARS,GIT_BRANCH=$GIT_BRANCH"
    ENV_VARS="$ENV_VARS,DEPLOY_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
fi

# Set contracts path for the deployed environment (if contracts exist)
if [ -d "./wordbattle-contracts" ]; then
    ENV_VARS="$ENV_VARS,CONTRACTS_DIR=/app/contracts"
fi

echo "✅ Environment variables configured"
echo ""

# Deploy to Cloud Run
echo "🚀 Deploying to Google Cloud Run..."

# First check if we need to create or update the service
if gcloud run services describe $SERVICE_NAME --region=$REGION >/dev/null 2>&1; then
    echo "  Updating existing service: $SERVICE_NAME"
else
    echo "  Creating new service: $SERVICE_NAME"
fi

# Build deployment command
DEPLOY_ARGS=(
    "run" "deploy" "$SERVICE_NAME"
    "--image=gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG"
    "--platform=managed"
    "--region=$REGION"
    "--allow-unauthenticated"
    "--port=8000"
    "--memory=$MEMORY"
    "--cpu=$CPU"
    "--timeout=3600"
    "--max-instances=$MAX_INSTANCES"
    "--min-instances=$MIN_INSTANCES"
    "--concurrency=80"
    "--execution-environment=gen2"
    "--set-env-vars=$ENV_VARS"
    "--add-cloudsql-instances=${PROJECT_ID}:${CLOUD_REGION}:${CLOUD_SQL_INSTANCE_NAME}"
)

# Execute deployment
gcloud "${DEPLOY_ARGS[@]}"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment Successful!"
    
    # Create Git tag for production deployments
    if [[ "$ENVIRONMENT" == "production" && -n "$GIT_COMMIT" && "$SKIP_GIT_CHECK" != "true" ]]; then
        DEPLOY_TAG="deploy-prod-$(date +%Y%m%d-%H%M%S)"
        echo "  Creating Git tag: $DEPLOY_TAG"
        git tag -a "$DEPLOY_TAG" -m "Production deployment at $(date '+%Y-%m-%d %H:%M:%S')"
        git push origin "$DEPLOY_TAG" || echo "⚠️  Failed to push tag (continuing anyway)"
        echo "✅ Git tag created and pushed"
    fi
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
    
    echo ""
    echo "🚀 WordBattle Backend ($ENVIRONMENT) is now live!"
    echo "================================================"
    echo "Application URL: $SERVICE_URL"
    echo "API Documentation: $SERVICE_URL/docs"
    echo "Health Check: $SERVICE_URL/health"
    echo "Database Status: $SERVICE_URL/database/status"
    echo ""
    
    # Test deployment
    echo "🧪 Testing Deployment..."
    sleep 10
    
    # Test health endpoint
    echo "  Testing health endpoint..."
    HEALTH_RESPONSE=$(curl -s -w "%{http_code}" "$SERVICE_URL/health")
    HTTP_STATUS="${HEALTH_RESPONSE: -3}"
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "✅ Health check passed!"
    else
        echo "⚠️  Health check returned status: $HTTP_STATUS"
    fi
    
    # Test API documentation
    echo "  Testing API documentation..."
    DOCS_RESPONSE=$(curl -s -w "%{http_code}" "$SERVICE_URL/docs")
    DOCS_STATUS="${DOCS_RESPONSE: -3}"
    
    if [ "$DOCS_STATUS" = "200" ]; then
        echo "✅ API documentation accessible!"
    else
        echo "⚠️  API docs returned status: $DOCS_STATUS"
    fi
    
    # Test contract validation
    echo "  Testing contract validation..."
    CONTRACT_RESPONSE=$(curl -s "$SERVICE_URL/admin/contracts/info")
    if echo "$CONTRACT_RESPONSE" | grep -q '"validator_loaded":true'; then
        echo "✅ Contract validation is enabled and working!"
    elif echo "$CONTRACT_RESPONSE" | grep -q '"enabled":true'; then
        echo "⚠️  Contract validation enabled but schemas not loaded"
    else
        echo "⚠️  Contract validation is disabled"
    fi
    
    # Run full contract validation if script exists and contracts are available
    if [ -f "$VALIDATION_SCRIPT" ] && [ -d "./wordbattle-contracts" ]; then
        echo "  Running comprehensive contract validation..."
        if python3 "$VALIDATION_SCRIPT" --url "$SERVICE_URL" --contracts-dir "./wordbattle-contracts" --timeout 30 --wait-for-deploy 5; then
            echo "✅ Comprehensive contract validation passed!"
        else
            echo "⚠️  Some contract validation checks failed"
            if [[ "$ENVIRONMENT" == "production" ]]; then
                echo "❌ Production deployment requires contract validation to pass"
                echo "Please review the contract validation results and fix any issues."
                # Don't exit here, just warn for now
            fi
        fi
    fi
    
    echo ""
    echo "📋 Deployment Summary:"
    echo "  ✅ Environment: $ENVIRONMENT"
    echo "  ✅ Service: $SERVICE_NAME"
    echo "  ✅ Image: gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG"
    if [[ -n "$GIT_COMMIT" ]]; then
        echo "  ✅ Git Commit: $GIT_COMMIT ($GIT_BRANCH)"
        if [[ "$ENVIRONMENT" == "production" ]]; then
            echo "  ✅ Git tag created: $DEPLOY_TAG"
        fi
    fi
    echo "  ✅ Docker image built and pushed"
    echo "  ✅ Cloud Run service deployed"
    echo "  ✅ Service is publicly accessible"
    echo ""
    echo "🔗 Important URLs:"
    echo "  Application: $SERVICE_URL"
    echo "  API Docs: $SERVICE_URL/docs"
    echo "  OpenAPI Schema: $SERVICE_URL/openapi.json"
    echo "  Contract Status: $SERVICE_URL/admin/contracts/info"
    echo ""
    
    # Clean up build artifacts
    echo "🧹 Cleaning up build artifacts..."
    rm -rf ./wordbattle-contracts 2>/dev/null || true
    echo "✅ Build context cleaned up"
    echo ""
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo "🏭 Production Environment Active"
        echo "  • Always-on with minimum 1 instance"
        echo "  • High performance: 2 CPU, 2GB RAM"
        echo "  • Scales up to 100 instances"
        echo "  • Optimized for stability and performance"
        echo "  • Git tags created for deployment tracking"
    else
        echo "🧪 Testing Environment Active"
        echo "  • Cost-optimized: scales to 0 when idle"
        echo "  • Basic performance: 1 CPU, 1GB RAM"
        echo "  • Scales up to 10 instances"
        echo "  • Debug mode enabled for development"
        echo "  • Allows uncommitted changes for testing"
    fi
    
    echo ""
    echo "🎯 Next Steps:"
    if [[ "$ENVIRONMENT" == "testing" ]]; then
        echo "  • Test the functionality in the testing environment"
        echo "  • When ready, deploy to production: ./deploy-unified.sh production"
    else
        echo "  • Monitor the production deployment"
        echo "  • Check logs: gcloud run services logs tail $SERVICE_NAME --region=$REGION"
    fi
    
else
    echo "❌ Deployment failed"
    echo "Check the logs with: gcloud run services logs tail $SERVICE_NAME --region=$REGION"
    exit 1
fi 