#!/bin/bash

# Test Development Script - Simple commands for test environment with branch support
set -e

TEST_URL="https://wordbattle-backend-test-441752988736.europe-west1.run.app"
TEST_BRANCH="test-environment"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function show_help() {
    echo -e "${BLUE}Test Development Commands:${NC}"
    echo "  ./test-dev.sh run          - Run all tests locally"
    echo "  ./test-dev.sh quick        - Run quick tests (exclude slow ones)"
    echo "  ./test-dev.sh deploy       - Deploy current branch to test"
    echo "  ./test-dev.sh test-branch  - Create/switch to test branch for changes"
    echo "  ./test-dev.sh merge-test   - Merge test branch back to main"
    echo "  ./test-dev.sh status       - Check test environment status"
    echo "  ./test-dev.sh logs         - Show recent deployment logs"
    echo "  ./test-dev.sh reset-db     - Reset test database"
    echo "  ./test-dev.sh branch-info  - Show current branch info"
    echo "  ./test-dev.sh help         - Show this help"
}

function run_tests() {
    echo -e "${BLUE}Running all tests...${NC}"
    python -m pytest tests/ -v
}

function run_quick_tests() {
    echo -e "${BLUE}Running quick tests...${NC}"
    python -m pytest tests/ -v -m "not slow" --maxfail=3
}

function create_test_branch() {
    current_branch=$(git branch --show-current)
    echo -e "${BLUE}Creating/switching to test branch...${NC}"
    
    if [ "$current_branch" != "main" ]; then
        echo -e "${YELLOW}Currently on branch: ${current_branch}${NC}"
        read -p "Switch to main first? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git checkout main
            git pull origin main
        fi
    fi
    
    # Check if test-environment branch exists
    if git show-ref --verify --quiet refs/heads/$TEST_BRANCH; then
        echo -e "${YELLOW}Test branch ${TEST_BRANCH} exists. Switching to it...${NC}"
        git checkout $TEST_BRANCH
        git pull origin $TEST_BRANCH
    else
        echo -e "${YELLOW}Creating new test branch: ${TEST_BRANCH}${NC}"
        git checkout -b $TEST_BRANCH
    fi
    
    echo -e "${GREEN}Now on test branch: ${TEST_BRANCH}${NC}"
    echo -e "${BLUE}You can now make your changes and test them safely!${NC}"
}

function merge_test_branch() {
    current_branch=$(git branch --show-current)
    
    if [ "$current_branch" != "$TEST_BRANCH" ]; then
        echo -e "${RED}You're not on the test branch (${TEST_BRANCH})${NC}"
        echo -e "${YELLOW}Current branch: ${current_branch}${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Merging test branch back to main...${NC}"
    
    # Make sure everything is committed
    if ! git diff --quiet; then
        echo -e "${RED}You have uncommitted changes. Please commit them first.${NC}"
        git status
        return 1
    fi
    
    # Push test branch first
    git push origin $TEST_BRANCH
    
    # Switch to main and merge
    git checkout main
    git pull origin main
    git merge $TEST_BRANCH
    git push origin main
    
    echo -e "${GREEN}Test branch merged successfully!${NC}"
    echo -e "${YELLOW}You can now delete the test branch if no longer needed.${NC}"
}

function deploy_to_test() {
    current_branch=$(git branch --show-current)
    echo -e "${BLUE}Deploying current branch to test environment...${NC}"
    echo -e "${YELLOW}Current branch: ${current_branch}${NC}"
    
    if [ "$current_branch" = "$TEST_BRANCH" ]; then
        echo -e "${GREEN}Good! Deploying from test branch.${NC}"
    else
        echo -e "${YELLOW}Note: You're deploying from ${current_branch}, not the test branch.${NC}"
    fi
    
    ./deploy-test.sh
}

function show_branch_info() {
    current_branch=$(git branch --show-current)
    echo -e "${BLUE}Branch Information:${NC}"
    echo -e "${YELLOW}Current branch: ${current_branch}${NC}"
    echo -e "${YELLOW}Test branch: ${TEST_BRANCH}${NC}"
    
    if [ "$current_branch" = "main" ]; then
        echo -e "${GREEN}✓ On main branch - safe for production work${NC}"
    elif [ "$current_branch" = "$TEST_BRANCH" ]; then
        echo -e "${GREEN}✓ On test branch - safe for experimental changes${NC}"
    else
        echo -e "${RED}⚠ On other branch - consider switching to main or test branch${NC}"
    fi
    
    echo -e "\n${BLUE}Recent commits:${NC}"
    git log --oneline -5
}

function check_status() {
    echo -e "${BLUE}Checking test environment status...${NC}"
    echo -e "${YELLOW}Test URL: ${TEST_URL}${NC}"
    
    echo -e "\n${GREEN}Health check:${NC}"
    curl -s "${TEST_URL}/health" | jq 2>/dev/null || curl -s "${TEST_URL}/health"
    
    echo -e "\n${GREEN}Admin status:${NC}"
    curl -s "${TEST_URL}/admin/database/admin-status" | jq 2>/dev/null || curl -s "${TEST_URL}/admin/database/admin-status"
}

function show_logs() {
    echo -e "${BLUE}Showing recent deployment logs...${NC}"
    gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="wordbattle-backend-test"' --limit=20 --format="table(timestamp,severity,textPayload)" --project=wordbattle-1748668162
}

function reset_database() {
    echo -e "${YELLOW}Resetting test database...${NC}"
    echo -e "${RED}WARNING: This will delete all data in the test database!${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        curl -s -X POST "${TEST_URL}/admin/database/reset" | jq 2>/dev/null || curl -s -X POST "${TEST_URL}/admin/database/reset"
        echo -e "${GREEN}Database reset complete${NC}"
    else
        echo -e "${YELLOW}Database reset cancelled${NC}"
    fi
}

# Main script logic
case "${1:-help}" in
    "run")
        run_tests
        ;;
    "quick")
        run_quick_tests
        ;;
    "deploy")
        deploy_to_test
        ;;
    "test-branch")
        create_test_branch
        ;;
    "merge-test")
        merge_test_branch
        ;;
    "status")
        check_status
        ;;
    "logs")
        show_logs
        ;;
    "reset-db")
        reset_database
        ;;
    "branch-info")
        show_branch_info
        ;;
    "help"|*)
        show_help
        ;;
esac 