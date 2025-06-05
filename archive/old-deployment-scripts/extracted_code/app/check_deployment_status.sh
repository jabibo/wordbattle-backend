#!/bin/bash

# Check deployment status for WordBattle services
REGION="eu-central-1"

echo "🔍 Checking WordBattle Deployment Status"
echo "========================================"

# Function to check service status
check_service() {
    local service_name=$1
    local service_type=$2
    
    echo ""
    echo "📋 $service_type Service: $service_name"
    echo "----------------------------------------"
    
    # Get service ARN
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local service_arn="arn:aws:apprunner:$REGION:$account_id:service/$service_name"
    
    # Check if service exists and get status
    if aws apprunner describe-service --service-arn "$service_arn" --region "$REGION" >/dev/null 2>&1; then
        local service_info=$(aws apprunner describe-service --service-arn "$service_arn" --region "$REGION")
        local status=$(echo "$service_info" | jq -r '.Service.Status')
        local service_url=$(echo "$service_info" | jq -r '.Service.ServiceUrl')
        local created_at=$(echo "$service_info" | jq -r '.Service.CreatedAt')
        local updated_at=$(echo "$service_info" | jq -r '.Service.UpdatedAt')
        
        echo "Status: $status"
        echo "URL: https://$service_url"
        echo "Created: $created_at"
        echo "Updated: $updated_at"
        
        # Test health endpoint if service is running
        if [ "$status" = "RUNNING" ]; then
            echo ""
            echo "🧪 Testing health endpoint..."
            if curl -s -f "https://$service_url/health" >/dev/null; then
                echo "✅ Health check: PASSED"
            else
                echo "❌ Health check: FAILED"
            fi
            
            # Test API docs
            if curl -s -f "https://$service_url/docs" >/dev/null; then
                echo "✅ API docs: ACCESSIBLE"
            else
                echo "❌ API docs: NOT ACCESSIBLE"
            fi
        fi
    else
        echo "❌ Service not found or not accessible"
    fi
}

# Check production service
check_service "wordbattle-backend" "Production"

# Check staging service
check_service "wordbattle-backend-staging" "Staging"

echo ""
echo "🔗 Useful Links:"
echo "GitHub Actions: https://github.com/jabibo/wordbattle-backend/actions"
echo "AWS App Runner Console: https://console.aws.amazon.com/apprunner/home?region=$REGION"
echo ""
echo "💡 Tip: Run this script periodically to monitor deployment progress" 