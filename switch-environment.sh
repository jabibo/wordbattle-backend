#!/bin/bash

# Environment switching utility for WordBattle Backend
# This script helps switch between test and production environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
show_usage() {
    echo "Usage: $0 [test|prod|status|help]"
    echo ""
    echo "Commands:"
    echo "  test    - Deploy to test environment"
    echo "  prod    - Deploy to production environment"
    echo "  status  - Show current environment status"
    echo "  help    - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 test     # Deploy to test"
    echo "  $0 prod     # Deploy to production"
    echo "  $0 status   # Check environment status"
}

# Function to show environment status
show_status() {
    echo -e "${BLUE}📊 WordBattle Environment Status${NC}"
    echo "=================================="
    
    echo ""
    echo -e "${YELLOW}🧪 Test Environment${NC}"
    TEST_URL="https://wordbattle-backend-test-441752988736.europe-west1.run.app"
    if curl -f -s "$TEST_URL/" > /dev/null 2>&1; then
        echo -e "   Status: ${GREEN}✅ Running${NC}"
        echo "   URL: $TEST_URL"
        echo "   Health: $(curl -s "$TEST_URL/health" 2>/dev/null | jq -r '.status // "Unknown"')"
    else
        echo -e "   Status: ${RED}❌ Down${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}🚀 Production Environment${NC}"
    PROD_URL="https://wordbattle-backend-prod-441752988736.europe-west1.run.app"
    if curl -f -s "$PROD_URL/" > /dev/null 2>&1; then
        echo -e "   Status: ${GREEN}✅ Running${NC}"
        echo "   URL: $PROD_URL"
        echo "   Health: $(curl -s "$PROD_URL/health" 2>/dev/null | jq -r '.status // "Unknown"')"
        
        # Check wordlist status for production
        echo "   Wordlists: $(curl -s "$PROD_URL/admin/database/wordlist-status" 2>/dev/null | jq -r '.total_words // "Error"') words"
    else
        echo -e "   Status: ${RED}❌ Down${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}📋 Quick Links${NC}"
    echo "   Test Docs: $TEST_URL/docs"
    echo "   Test Debug: $TEST_URL/debug/tokens"
    echo "   Prod Docs: $PROD_URL/docs"
    echo "   Admin Panel: $PROD_URL/admin/database/wordlist-status"
}

# Function to deploy to test
deploy_test() {
    echo -e "${BLUE}🧪 Deploying to Test Environment...${NC}"
    ./deploy-test.sh
}

# Function to deploy to production
deploy_prod() {
    echo -e "${RED}🚀 Deploying to Production Environment...${NC}"
    echo -e "${YELLOW}⚠️  WARNING: This will deploy to production!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    
    if [[ $confirm == "yes" ]]; then
        ./deploy-production.sh
    else
        echo "Production deployment cancelled."
        exit 0
    fi
}

# Main script logic
case "${1:-help}" in
    "test")
        deploy_test
        ;;
    "prod")
        deploy_prod
        ;;
    "status")
        show_status
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac 