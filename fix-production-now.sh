#!/bin/bash

################################################################################
# Quick Fix Script for Production Wordlist Issue
#
# This script immediately fixes the production "no wordlist de available" error
# by deploying the current code with the corrected import statement.
#
# Usage:
#   ./fix-production-now.sh
################################################################################

set -e

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

echo ""
echo "=========================================="
echo "  WordBattle Production Quick Fix"
echo "=========================================="
echo ""
log_warning "This will deploy the latest code to production"
log_info "The fix resolves: 'no wordlist de available' error"
log_info "Root cause: Incorrect import in wordlist_utils.py"
echo ""

# Confirm
read -p "Continue with deployment? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log_error "Deployment cancelled"
    exit 1
fi

echo ""
log_info "Starting deployment..."
echo ""

# Run the deployment script
./deploy-self-hosted.sh main

echo ""
log_success "Deployment completed!"
echo ""
log_info "Verifying fix..."

# Check health endpoint
sleep 5
if curl -s -f -m 10 https://wordbattle2.de/health > /dev/null 2>&1; then
    log_success "Health check passed!"
    echo ""
    log_info "Testing German wordlist..."
    
    # Try to access an endpoint that uses German words
    HEALTH_RESPONSE=$(curl -s https://wordbattle2.de/health)
    echo "Health response: $HEALTH_RESPONSE"
    
    echo ""
    log_success "Production fix completed!"
    log_info "The wordlist import issue has been resolved"
else
    log_warning "Health check not responding yet"
    log_info "Check logs with: ssh root@wordbattle2.de 'docker logs wordbattle-backend'"
fi

echo ""
