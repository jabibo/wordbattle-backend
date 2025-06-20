#!/bin/bash

# WordBattle Backend - Test Environment Deployment
# Simple wrapper for testing environment deployment

echo "🧪 Deploying to Test Environment"
echo "================================"
echo ""

# Call the unified script with testing environment
./deploy-unified.sh testing "$@" 