#!/usr/bin/env python3

import requests
import json

BASE_URL = "https://wordbattle-backend-skhco4fxoq-ew.a.run.app"

def test_production_endpoints():
    """Test what the production endpoints actually return."""
    
    print("🔍 Testing Production API Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        health_data = response.json()
        print(f"✅ Health: {health_data}")
    else:
        print(f"❌ Health failed: {response.status_code}")
    
    # Test API documentation endpoint to see the schema
    print("\n2. Testing API schema...")
    response = requests.get(f"{BASE_URL}/openapi.json")
    if response.status_code == 200:
        schema = response.json()
        
        # Check if move endpoint exists and what it returns
        move_path = schema.get("paths", {}).get("/games/{game_id}/move", {})
        if move_path:
            print("✅ Move endpoint found in schema")
            post_method = move_path.get("post", {})
            responses = post_method.get("responses", {})
            success_response = responses.get("200", {})
            content = success_response.get("content", {})
            app_json = content.get("application/json", {})
            response_schema = app_json.get("schema", {})
            
            print(f"Move endpoint response schema: {json.dumps(response_schema, indent=2)}")
        else:
            print("❌ Move endpoint not found in schema")
            
        # Check test-move endpoint
        test_move_path = schema.get("paths", {}).get("/games/{game_id}/test-move", {})
        if test_move_path:
            print("✅ Test-move endpoint found in schema")
            post_method = test_move_path.get("post", {})
            responses = post_method.get("responses", {})
            success_response = responses.get("200", {})
            content = success_response.get("content", {})
            app_json = content.get("application/json", {})
            response_schema = app_json.get("schema", {})
            
            print(f"Test-move endpoint response schema: {json.dumps(response_schema, indent=2)}")
        else:
            print("❌ Test-move endpoint not found in schema")
    else:
        print(f"❌ Schema request failed: {response.status_code}")
    
    # Test authentication to see what happens
    print("\n3. Testing move endpoint without auth...")
    response = requests.post(f"{BASE_URL}/games/test-game-id/move", json=[])
    print(f"Move endpoint (no auth): {response.status_code} - {response.text[:200]}")
    
    print("\n4. Testing test-move endpoint without auth...")
    response = requests.post(f"{BASE_URL}/games/test-game-id/test-move", json={"move_data": []})
    print(f"Test-move endpoint (no auth): {response.status_code} - {response.text[:200]}")

if __name__ == "__main__":
    test_production_endpoints() 