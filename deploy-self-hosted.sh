#!/bin/bash

################################################################################
# WordBattle Self-Hosted Deployment Script
#
# This script automates deployment to wordbattle2.de by:
# 1. Pulling latest code from git on the server
# 2. Building a new Docker image
# 3. Stopping the old container
# 4. Starting a new container with the updated image
#
# Usage:
#   ./deploy-self-hosted.sh [branch]
#
# Examples:
#   ./deploy-self-hosted.sh              # Deploy current/default branch
#   ./deploy-self-hosted.sh main         # Deploy specific branch
#   ./deploy-self-hosted.sh feature/xyz  # Deploy feature branch
################################################################################

set -e  # Exit on error

# Configuration
SERVER="wordbattle2.de"
SERVER_USER="root"
APP_DIR="/home/wordbattle/wordbattle"
CONTAINER_NAME="wordbattle-backend"
IMAGE_NAME="wordbattle-backend"
COMPOSE_FILE="docker-compose.production.yml"
GIT_REPO="https://github.com/jabibo/wordbattle-backend.git"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

log_success() {
    echo -e "${GREEN}✅ ${NC}$1"
}

log_warning() {
    echo -e "${YELLOW}⚠️  ${NC}$1"
}

log_error() {
    echo -e "${RED}❌ ${NC}$1"
}

# Parse arguments
BRANCH="${1:-main}"

echo ""
echo "=========================================="
echo "  WordBattle Self-Hosted Deployment"
echo "=========================================="
echo ""
log_info "Target server: ${SERVER}"
log_info "Target branch: ${BRANCH}"
log_info "Container: ${CONTAINER_NAME}"
echo ""

# Step 1: Check SSH connectivity
log_info "Step 1/7: Checking SSH connectivity..."
if ! ssh -o ConnectTimeout=10 "${SERVER_USER}@${SERVER}" "echo 'SSH connection successful'" > /dev/null 2>&1; then
    log_error "Cannot connect to ${SERVER}. Please check your SSH connection."
    exit 1
fi
log_success "SSH connection established"
echo ""

# Step 2: Initialize or update git repository on server
log_info "Step 2/7: Setting up git repository on server..."

ssh "${SERVER_USER}@${SERVER}" bash << 'ENDSSH'
set -e

APP_DIR="/home/wordbattle/wordbattle"
GIT_REPO="https://github.com/jabibo/wordbattle-backend.git"
BRANCH="$1"

cd "${APP_DIR}"

# Check if .git directory exists
if [ ! -d ".git" ]; then
    echo "Git repository not found. Initializing..."
    
    # Backup current app directory
    BACKUP_DIR="${APP_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "Creating backup at ${BACKUP_DIR}..."
    cd ..
    cp -r wordbattle "${BACKUP_DIR}"
    cd "${APP_DIR}"
    
    # Initialize git repository
    git init
    git remote add origin "${GIT_REPO}"
    git fetch origin
    
    # Check if branch exists remotely
    if git ls-remote --heads origin "${BRANCH}" | grep -q "${BRANCH}"; then
        git checkout -b "${BRANCH}" "origin/${BRANCH}" || {
            echo "Checkout failed, forcing with -f..."
            git checkout -f -b "${BRANCH}" "origin/${BRANCH}"
        }
    else
        echo "Branch ${BRANCH} not found. Using main/master..."
        if git ls-remote --heads origin main | grep -q main; then
            git checkout -f -b main origin/main
        else
            git checkout -f -b master origin/master
        fi
    fi
    
    echo "Git repository initialized"
else
    echo "Git repository found. Updating..."
    
    # Stash any local changes
    if ! git diff-index --quiet HEAD --; then
        echo "Local changes detected. Stashing..."
        git stash
    fi
    
    # Fetch latest changes
    git fetch origin
    
    # Checkout target branch
    if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
        git checkout "${BRANCH}"
    else
        git checkout -b "${BRANCH}" "origin/${BRANCH}" 2>/dev/null || {
            echo "Branch ${BRANCH} not found remotely"
            exit 1
        }
    fi
    
    # Pull latest changes
    git pull origin "${BRANCH}" || {
        echo "Warning: Could not pull from origin. Using local version."
    }
    
    echo "Git repository updated"
fi

# Show current commit
echo "Current commit:"
git log -1 --oneline

ENDSSH

log_success "Git repository ready"
echo ""

# Step 3: Build new Docker image
log_info "Step 3/7: Building new Docker image..."

ssh "${SERVER_USER}@${SERVER}" bash << 'ENDSSH'
set -e

APP_DIR="/home/wordbattle/wordbattle"
IMAGE_NAME="wordbattle-backend"

cd "${APP_DIR}"

# Get git commit hash for tagging
GIT_COMMIT=$(git rev-parse --short HEAD)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Build the image with multiple tags
echo "Building image: ${IMAGE_NAME}:${TIMESTAMP}-${GIT_COMMIT}"

docker build -t "${IMAGE_NAME}:latest" \
    -t "${IMAGE_NAME}:${TIMESTAMP}-${GIT_COMMIT}" \
    -f Dockerfile \
    .

echo "Docker image built successfully"
echo "Tagged as: ${IMAGE_NAME}:latest"
echo "Tagged as: ${IMAGE_NAME}:${TIMESTAMP}-${GIT_COMMIT}"

ENDSSH

log_success "Docker image built"
echo ""

# Step 4: Create backup of current container state
log_info "Step 4/7: Creating backup of current state..."

ssh "${SERVER_USER}@${SERVER}" bash << 'ENDSSH'
set -e

APP_DIR="/home/wordbattle/wordbattle"
CONTAINER_NAME="wordbattle-backend"
BACKUP_DIR="/home/wordbattle/backups"

mkdir -p "${BACKUP_DIR}"

# Export current container image (if running)
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    CURRENT_IMAGE=$(docker inspect "${CONTAINER_NAME}" --format '{{.Image}}' 2>/dev/null || echo "none")
    echo "Current container image: ${CURRENT_IMAGE}"
    
    # Tag current image as backup
    if [ "${CURRENT_IMAGE}" != "none" ]; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        docker tag "${CURRENT_IMAGE}" "wordbattle-backend:backup-${TIMESTAMP}" 2>/dev/null || true
        echo "Current image backed up as: wordbattle-backend:backup-${TIMESTAMP}"
    fi
fi

ENDSSH

log_success "Backup created"
echo ""

# Step 5: Stop and remove old container
log_info "Step 5/7: Stopping old container..."

ssh "${SERVER_USER}@${SERVER}" bash << 'ENDSSH'
set -e

APP_DIR="/home/wordbattle/wordbattle"
COMPOSE_FILE="docker-compose.production.yml"

cd "${APP_DIR}"

# Stop the backend container using docker-compose
if [ -f "${COMPOSE_FILE}" ]; then
    docker-compose -f "${COMPOSE_FILE}" stop wordbattle-backend 2>/dev/null || true
    docker-compose -f "${COMPOSE_FILE}" rm -f wordbattle-backend 2>/dev/null || true
else
    # Fallback to direct docker commands
    docker stop wordbattle-backend 2>/dev/null || true
    docker rm wordbattle-backend 2>/dev/null || true
fi

echo "Old container stopped and removed"

ENDSSH

log_success "Old container removed"
echo ""

# Step 6: Start new container
log_info "Step 6/7: Starting new container..."

ssh "${SERVER_USER}@${SERVER}" bash << 'ENDSSH'
set -e

APP_DIR="/home/wordbattle/wordbattle"
COMPOSE_FILE="docker-compose.production.yml"

cd "${APP_DIR}"

# Start the backend container using docker-compose
if [ -f "${COMPOSE_FILE}" ]; then
    docker-compose -f "${COMPOSE_FILE}" up -d wordbattle-backend
else
    echo "Error: ${COMPOSE_FILE} not found"
    exit 1
fi

echo "New container started"

# Wait for container to be healthy
echo "Waiting for container to be healthy..."
sleep 10

# Check container status
CONTAINER_STATUS=$(docker inspect wordbattle-backend --format '{{.State.Status}}' 2>/dev/null || echo "not found")
echo "Container status: ${CONTAINER_STATUS}"

if [ "${CONTAINER_STATUS}" != "running" ]; then
    echo "Warning: Container is not running. Checking logs..."
    docker logs --tail 50 wordbattle-backend
    exit 1
fi

ENDSSH

log_success "New container started"
echo ""

# Step 7: Verify deployment
log_info "Step 7/7: Verifying deployment..."

sleep 5

# Check health endpoint
log_info "Testing health endpoint..."
if curl -s -f -m 10 https://wordbattle2.de/health > /dev/null 2>&1; then
    log_success "Health check passed"
else
    log_warning "Health check failed or not responding yet"
    log_info "Checking container logs..."
    ssh "${SERVER_USER}@${SERVER}" "docker logs --tail 30 wordbattle-backend"
fi

echo ""

# Show deployment summary
ssh "${SERVER_USER}@${SERVER}" bash << 'ENDSSH'
APP_DIR="/home/wordbattle/wordbattle"
cd "${APP_DIR}"

echo "=========================================="
echo "  Deployment Summary"
echo "=========================================="
echo ""
echo "Git commit:"
git log -1 --oneline
echo ""
echo "Container status:"
docker ps --filter "name=wordbattle-backend" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
echo ""
echo "Recent logs:"
docker logs --tail 10 wordbattle-backend 2>&1 | grep -v "DEBUG" || true
echo ""

ENDSSH

log_success "Deployment completed!"
echo ""
log_info "Access your application at: https://wordbattle2.de"
log_info "API documentation: https://wordbattle2.de/docs"
log_info "Health check: https://wordbattle2.de/health"
echo ""
log_warning "Monitor logs with: ssh ${SERVER_USER}@${SERVER} 'docker logs -f wordbattle-backend'"
echo ""
