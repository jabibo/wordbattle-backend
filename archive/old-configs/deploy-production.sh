#!/bin/bash

# WordBattle Backend - Production Environment Deployment
# Simple wrapper for production environment deployment

echo "🏭 Deploying to Production Environment"
echo "======================================"
echo ""

# Call the unified script with production environment
./deploy-unified.sh production "$@" 