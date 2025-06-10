#!/bin/bash
echo "Testing test environment after permission fix..."
TEST_URL="https://wordbattle-backend-test-441752988736.europe-west1.run.app"

echo "Admin status test:"
curl -s "$TEST_URL/admin/database/admin-status" | jq 2>/dev/null || curl -s "$TEST_URL/admin/database/admin-status"

echo ""
echo "Create admin user test:"
curl -s -X POST "$TEST_URL/admin/database/create-default-admin" | jq 2>/dev/null || curl -s -X POST "$TEST_URL/admin/database/create-default-admin"
