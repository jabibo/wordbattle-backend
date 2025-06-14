#!/bin/bash

# Updated deploy to test environment script - now uses robust deployment
echo "🚀 Deploying to test environment with robust deployment script..."

# Check if the robust deployment script exists
if [ -f "./deploy-test-robust.sh" ]; then
    echo "Using robust deployment script for testing deployment..."
    ./deploy-test-robust.sh
else
    echo "⚠️  Robust deployment script not found, falling back to original method..."
    
    # Check if the main deployment script exists
    if [ -f "./deploy-gcp-production.sh" ]; then
        echo "Using deploy-gcp-production.sh for testing deployment..."
        ./deploy-gcp-production.sh testing
    elif [ -f "./deploy-gcp-production.ps1" ]; then
        echo "Using PowerShell deployment script for testing..."
        pwsh ./deploy-gcp-production.ps1 -Environment testing
    else
        echo "❌ No deployment script found!"
        echo "Available files:"
        ls -la *.sh *.ps1 2>/dev/null || echo "No deployment scripts found"
        exit 1
    fi
fi 