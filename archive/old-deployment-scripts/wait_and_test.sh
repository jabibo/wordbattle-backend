#!/bin/bash

# Wait for App Runner deployment to complete and test endpoints
SERVICE_ARN="arn:aws:apprunner:eu-central-1:598510278922:service/wordbattle-backend"
REGION="eu-central-1"
URL="https://nmexamntve.eu-central-1.awsapprunner.com"

echo "🚀 Waiting for WordBattle Deployment to Complete"
echo "================================================"

# Function to check service status
check_status() {
    aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$REGION" | jq -r '.Service.Status'
}

# Wait for deployment to complete
echo "⏳ Waiting for App Runner service to be ready..."
max_wait=600  # 10 minutes
wait_interval=30  # 30 seconds
elapsed=0

while [ $elapsed -lt $max_wait ]; do
    status=$(check_status)
    echo "   Current status: $status (${elapsed}s elapsed)"
    
    if [ "$status" = "RUNNING" ]; then
        echo "✅ Service is now RUNNING!"
        break
    elif [ "$status" = "CREATE_FAILED" ] || [ "$status" = "UPDATE_FAILED" ]; then
        echo "❌ Deployment failed with status: $status"
        exit 1
    fi
    
    sleep $wait_interval
    elapsed=$((elapsed + wait_interval))
done

if [ $elapsed -ge $max_wait ]; then
    echo "⚠️ Timeout reached. Service may still be deploying."
    echo "Current status: $(check_status)"
fi

echo ""
echo "🧪 Testing Updated Endpoints"
echo "============================"

# Test 1: Debug tokens endpoint
echo "1. Testing debug tokens endpoint..."
debug_response=$(curl -s "$URL/debug/tokens")

if echo "$debug_response" | grep -q '"player01"'; then
    echo "✅ SUCCESS: Debug endpoint updated to lowercase format!"
    echo "   Found keys: $(echo "$debug_response" | jq -r '.tokens | keys | join(", ")')"
else
    echo "⏳ Debug endpoint still using old format"
    echo "   Current keys: $(echo "$debug_response" | jq -r '.tokens | keys | join(", ")')"
fi

echo ""

# Test 2: Admin endpoint
echo "2. Testing admin create-test-tokens endpoint..."
admin_response=$(curl -s -X POST "$URL/admin/debug/create-test-tokens")

if echo "$admin_response" | grep -q '@binge.de'; then
    echo "✅ SUCCESS: Admin endpoint updated with @binge.de emails!"
    echo ""
    echo "📧 Test user details:"
    echo "$admin_response" | jq -r '.users[]? | "   \(.username): \(.email)"'
elif echo "$admin_response" | grep -q 'Not Found'; then
    echo "❌ Admin endpoint not found (may not be deployed yet)"
else
    echo "⏳ Admin endpoint exists but not yet updated"
    echo "   Response: $(echo "$admin_response" | jq -r '.message // .detail // "Unknown response"')"
fi

echo ""
echo "🔗 Service Information:"
echo "   Production URL: $URL"
echo "   API Documentation: $URL/docs"
echo "   Health Check: $URL/health"
echo "   Service Status: $(check_status)"

# Final test of the new functionality
echo ""
echo "🎯 Final Test: Creating test users with @binge.de emails"
echo "========================================================"

if echo "$admin_response" | grep -q '@binge.de'; then
    echo "✅ DEPLOYMENT SUCCESSFUL!"
    echo ""
    echo "The test users now have the correct email addresses:"
    echo "$admin_response" | jq -r '.users[]? | "   • \(.username) → \(.email)"'
    echo ""
    echo "🎉 You can now easily test invitations using these @binge.de addresses!"
else
    echo "⚠️ Deployment may still be in progress or there was an issue."
    echo "   Please check the GitHub Actions logs or try again in a few minutes."
fi 