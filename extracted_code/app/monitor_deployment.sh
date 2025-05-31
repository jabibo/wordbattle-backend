#!/bin/bash

# Monitor GitHub Actions deployment and test endpoints
REPO="jabibo/wordbattle-backend"
PRODUCTION_URL="https://nmexamntve.eu-central-1.awsapprunner.com"

echo "🔄 Monitoring WordBattle Deployment"
echo "=================================="

# Function to check GitHub Actions status
check_github_actions() {
    echo "📋 Checking GitHub Actions status..."
    local runs=$(curl -s "https://api.github.com/repos/$REPO/actions/runs?per_page=3")
    
    echo "$runs" | jq -r '.workflow_runs[] | select(.head_branch == "production" or .head_branch == "main") | "Branch: \(.head_branch) | Status: \(.status) | Conclusion: \(.conclusion // "running") | Created: \(.created_at)"'
}

# Function to test the updated endpoints
test_endpoints() {
    echo ""
    echo "🧪 Testing Updated Endpoints"
    echo "----------------------------"
    
    # Test debug tokens endpoint
    echo "1. Testing debug tokens endpoint..."
    local debug_response=$(curl -s "$PRODUCTION_URL/debug/tokens")
    
    # Check if response contains the new lowercase format
    if echo "$debug_response" | grep -q '"player01"'; then
        echo "✅ Debug endpoint updated - using lowercase usernames"
    else
        echo "⏳ Debug endpoint not yet updated - still using old format"
    fi
    
    # Test admin endpoint
    echo ""
    echo "2. Testing admin create-test-tokens endpoint..."
    local admin_response=$(curl -s -X POST "$PRODUCTION_URL/admin/debug/create-test-tokens")
    
    if echo "$admin_response" | grep -q '@binge.de'; then
        echo "✅ Admin endpoint updated - using @binge.de email addresses"
        echo ""
        echo "📧 Test user emails:"
        echo "$admin_response" | jq -r '.users[]? | "  \(.username): \(.email)"'
    elif echo "$admin_response" | grep -q 'Not Found'; then
        echo "⏳ Admin endpoint not yet available (deployment in progress)"
    else
        echo "⏳ Admin endpoint not yet updated"
    fi
}

# Function to wait for deployment completion
wait_for_deployment() {
    local max_wait=600  # 10 minutes
    local wait_interval=30  # 30 seconds
    local elapsed=0
    
    echo ""
    echo "⏳ Waiting for deployment to complete..."
    echo "   Max wait time: $((max_wait/60)) minutes"
    
    while [ $elapsed -lt $max_wait ]; do
        local runs=$(curl -s "https://api.github.com/repos/$REPO/actions/runs?per_page=2")
        local in_progress=$(echo "$runs" | jq -r '.workflow_runs[] | select(.head_branch == "production" or .head_branch == "main") | select(.status == "in_progress") | .id')
        
        if [ -z "$in_progress" ]; then
            echo "✅ All deployments completed!"
            return 0
        fi
        
        echo "   Still deploying... (${elapsed}s elapsed)"
        sleep $wait_interval
        elapsed=$((elapsed + wait_interval))
    done
    
    echo "⚠️ Timeout reached. Deployment may still be in progress."
    return 1
}

# Main execution
check_github_actions
echo ""

# Wait for deployment to complete
if wait_for_deployment; then
    echo ""
    echo "🎉 Testing the deployed changes..."
    test_endpoints
else
    echo ""
    echo "🔍 Testing current state (deployment may still be ongoing)..."
    test_endpoints
fi

echo ""
echo "🔗 Useful Links:"
echo "GitHub Actions: https://github.com/$REPO/actions"
echo "Production API: $PRODUCTION_URL"
echo "API Documentation: $PRODUCTION_URL/docs"
echo "Health Check: $PRODUCTION_URL/health" 