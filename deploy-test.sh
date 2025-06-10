#!/bin/bash

# Simple deploy to test environment script
echo "🚀 Deploying to test environment..."

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