#!/bin/bash

# WordBattle Backend - Production Environment Deployment
# This script deploys to the production environment using the unified deployment script.
# 
# Legacy script maintained for backward compatibility.
# For new deployments, use: ./deploy-unified.sh production

ENVIRONMENT=${1:-production}

echo "🏭 WordBattle Backend - Production Environment Deployment"
echo "========================================================"
echo "Target Environment: $ENVIRONMENT"
echo ""

# Check if the unified deployment script exists
if [ ! -f "./deploy-unified.sh" ]; then
    echo "❌ Unified deployment script not found!"
    echo "Expected: ./deploy-unified.sh"
    echo ""
    echo "The deployment system has been refactored. Please use the unified script:"
    echo "  ./deploy-unified.sh production"
    exit 1
fi

# Show deprecation notice for direct production script usage
if [[ "$ENVIRONMENT" == "production" ]]; then
    echo "⚠️  DEPRECATION NOTICE:"
    echo "This script is maintained for backward compatibility."
    echo "For new deployments, please use: ./deploy-unified.sh production"
    echo ""
    echo "Continuing with deployment in 5 seconds..."
    sleep 5
fi

# Forward all arguments to the unified script
echo "🔄 Using unified deployment script for $ENVIRONMENT environment..."
echo "Arguments passed: $@"
echo ""

# Call the unified script with the specified environment
./deploy-unified.sh "$@" 