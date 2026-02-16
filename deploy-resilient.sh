#!/bin/bash

################################################################################
# Resilient Self-Hosted Deployment Script
#
# This version includes retry logic for unstable SSH connections
################################################################################

set -e

# Configuration
SERVER="wordbattle2.de"
SERVER_USER="root"
APP_DIR="/home/wordbattle/wordbattle"
CONTAINER_NAME="wordbattle-backend"
IMAGE_NAME="wordbattle-backend"
COMPOSE_FILE="docker-compose.production.yml"
GIT_REPO="https://github.com/jabibo/wordbattle-backend.git"
MAX_RETRIES=3
RETRY_DELAY=5

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ ${NC}$1"; }
log_success() { echo -e "${GREEN}✅ ${NC}$1"; }
log_warning() { echo -e "${YELLOW}⚠️  ${NC}$1"; }
log_error() { echo -e "${RED}❌ ${NC}$1"; }

# Function to execute SSH command with retries
ssh_retry() {
    local cmd="$1"
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        if ssh -o ConnectTimeout=10 "${SERVER_USER}@${SERVER}" "$cmd" 2>&1; then
            return 0
        else
            if [ $attempt -lt $MAX_RETRIES ]; then
                log_warning "SSH attempt $attempt failed, retrying in ${RETRY_DELAY}s..."
                sleep $RETRY_DELAY
                ((attempt++))
            else
                log_error "SSH failed after $MAX_RETRIES attempts"
                return 1
            fi
        fi
    done
}

# Function to execute SSH script with retries
ssh_script_retry() {
    local script="$1"
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        if ssh -o ConnectTimeout=10 "${SERVER_USER}@${SERVER}" bash <<< "$script" 2>&1; then
            return 0
        else
            if [ $attempt -lt $MAX_RETRIES ]; then
                log_warning "SSH attempt $attempt failed, retrying in ${RETRY_DELAY}s..."
                sleep $RETRY_DELAY
                ((attempt++))
            else
                log_error "SSH failed after $MAX_RETRIES attempts"
                return 1
            fi
        fi
    done
}

BRANCH="${1:-main}"

echo ""
echo "=========================================="
echo "  WordBattle Resilient Deployment"
echo "=========================================="
echo ""
log_info "Target server: ${SERVER}"
log_info "Target branch: ${BRANCH}"
echo ""

# Step 1: Check connectivity
log_info "Checking SSH connectivity..."
if ! ssh_retry "echo 'OK'" > /dev/null; then
    log_error "Cannot establish SSH connection"
    exit 1
fi
log_success "SSH connection established"
echo ""

# Step 2: Setup git
log_info "Setting up git repository..."
ssh_script_retry "
set -e
cd ${APP_DIR}
rm -rf .git
git init
git remote add origin ${GIT_REPO}
git fetch origin
git checkout -f -b ${BRANCH} origin/${BRANCH}
echo 'Git setup complete'
git log -1 --oneline
"
log_success "Git repository ready"
echo ""

# Step 3: Build Docker image
log_info "Building Docker image..."
ssh_script_retry "
set -e
cd ${APP_DIR}
GIT_COMMIT=\$(git rev-parse --short HEAD)
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
docker build -t ${IMAGE_NAME}:latest -t ${IMAGE_NAME}:\${TIMESTAMP}-\${GIT_COMMIT} -f Dockerfile .
echo \"Built: ${IMAGE_NAME}:\${TIMESTAMP}-\${GIT_COMMIT}\"
"
log_success "Docker image built"
echo ""

# Step 4: Backup current image
log_info "Creating backup..."
ssh_script_retry "
CURRENT_IMAGE=\$(docker inspect ${CONTAINER_NAME} --format '{{.Image}}' 2>/dev/null || echo 'none')
if [ \"\${CURRENT_IMAGE}\" != \"none\" ]; then
    TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
    docker tag \"\${CURRENT_IMAGE}\" \"${IMAGE_NAME}:backup-\${TIMESTAMP}\" 2>/dev/null || true
    echo \"Backup created: ${IMAGE_NAME}:backup-\${TIMESTAMP}\"
fi
"
log_success "Backup created"
echo ""

# Step 5: Stop old container
log_info "Stopping old container..."
ssh_script_retry "
cd ${APP_DIR}
docker-compose -f ${COMPOSE_FILE} stop ${CONTAINER_NAME} 2>/dev/null || true
docker-compose -f ${COMPOSE_FILE} rm -f ${CONTAINER_NAME} 2>/dev/null || true
echo 'Old container stopped'
"
log_success "Old container removed"
echo ""

# Step 6: Start new container
log_info "Starting new container..."
ssh_script_retry "
cd ${APP_DIR}
docker-compose -f ${COMPOSE_FILE} up -d ${CONTAINER_NAME}
sleep 10
docker ps --filter 'name=${CONTAINER_NAME}' --format '{{.Names}}\t{{.Status}}'
"
log_success "New container started"
echo ""

# Step 7: Verify
log_info "Verifying deployment..."
sleep 5
if curl -s -f -m 10 https://wordbattle2.de/health > /dev/null 2>&1; then
    log_success "Health check passed!"
else
    log_warning "Health check not responding yet"
    log_info "Check logs: ssh ${SERVER_USER}@${SERVER} 'docker logs ${CONTAINER_NAME}'"
fi

echo ""
log_success "Deployment completed!"
echo ""
log_info "Application: https://wordbattle2.de"
log_info "Health: https://wordbattle2.de/health"
echo ""
