#!/bin/bash

# WordBattle Backend - Testing Environment Deployment
# This script deploys to the testing environment using the unified deployment script.

echo "🧪 WordBattle Backend - Testing Environment Deployment"
echo "======================================================"
echo ""

# Check if the unified deployment script exists
if [ ! -f "./deploy-unified.sh" ]; then
    echo "❌ Unified deployment script not found!"
    echo "Expected: ./deploy-unified.sh"
    echo ""
    echo "The deployment system has been refactored. Please use the unified script:"
    echo "  ./deploy-unified.sh testing"
    exit 1
fi

# Forward all arguments to the unified script, but force testing environment
echo "🔄 Using unified deployment script for testing environment..."
echo "Arguments passed: $@"
echo ""

# Call the unified script with testing environment
./deploy-unified.sh testing "$@" 