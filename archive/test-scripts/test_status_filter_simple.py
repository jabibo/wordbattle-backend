import requests
import json

def test_status_filter_endpoint():
    """Simple test to check if the status_filter parameter is available"""
    print("🧪 Testing Status Filter Endpoint Implementation")
    print("=" * 50)
    
    backend_url = "https://wordbattle-backend-441752988736.europe-west1.run.app"
    
    # Test 1: Try the endpoint without authentication (should get 401 but not 404)
    print("1. Testing endpoint availability...")
    response = requests.get(f"{backend_url}/games/my-games", timeout=10)
    
    if response.status_code == 401:
        print("✅ Endpoint exists and requires authentication (expected)")
    elif response.status_code == 404:
        print("❌ Endpoint not found")
        return
    else:
        print(f"⚠️  Unexpected status code: {response.status_code}")
    
    # Test 2: Check with status_filter parameter
    print("\n2. Testing status_filter parameter...")
    response = requests.get(f"{backend_url}/games/my-games?status_filter=completed", timeout=10)
    
    if response.status_code == 401:
        print("✅ Endpoint with status_filter parameter exists and requires authentication")
    elif response.status_code == 400:
        error = response.json()
        if "Invalid status values" in str(error):
            print("❌ Status validation error - might be issue with parameter handling")
        else:
            print("⚠️  Different parameter validation error")
        print(f"   Error: {error}")
    elif response.status_code == 422:
        error = response.json()
        print(f"⚠️  Parameter parsing error: {error}")
    else:
        print(f"⚠️  Unexpected status code: {response.status_code}")
    
    # Test 3: Check API documentation (OpenAPI)
    print("\n3. Checking API documentation...")
    response = requests.get(f"{backend_url}/docs", timeout=10)
    
    if response.status_code == 200:
        print("✅ API docs accessible")
        # We could parse the OpenAPI spec to verify the parameter, but that's complex
    else:
        print(f"⚠️  API docs not accessible: {response.status_code}")
    
    # Test 4: Check OpenAPI JSON directly
    print("\n4. Checking OpenAPI spec...")
    response = requests.get(f"{backend_url}/openapi.json", timeout=10)
    
    if response.status_code == 200:
        try:
            openapi_spec = response.json()
            
            # Look for the my-games endpoint
            paths = openapi_spec.get("paths", {})
            my_games_path = paths.get("/games/my-games", {})
            get_method = my_games_path.get("get", {})
            parameters = get_method.get("parameters", [])
            
            # Check if status_filter parameter exists
            status_filter_param = None
            for param in parameters:
                if param.get("name") == "status_filter":
                    status_filter_param = param
                    break
            
            if status_filter_param:
                print("✅ status_filter parameter found in OpenAPI spec!")
                print(f"   Parameter details: {json.dumps(status_filter_param, indent=2)}")
            else:
                print("❌ status_filter parameter NOT found in OpenAPI spec")
                print(f"   Available parameters: {[p.get('name') for p in parameters]}")
                
        except json.JSONDecodeError:
            print("❌ Failed to parse OpenAPI spec")
    else:
        print(f"⚠️  OpenAPI spec not accessible: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 Status filter endpoint testing completed!")

if __name__ == "__main__":
    test_status_filter_endpoint() 