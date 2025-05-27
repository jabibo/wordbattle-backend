#!/usr/bin/env python3
"""
Check what endpoints are currently available on the deployed backend
"""
import requests

BACKEND_URL = "https://mnirejmq3g.eu-central-1.awsapprunner.com"

def check_endpoints():
    """Check what endpoints are available"""
    print("🔍 Checking Available Endpoints")
    print("=" * 40)
    
    # Check OpenAPI spec
    try:
        response = requests.get(f"{BACKEND_URL}/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})
            
            print(f"✅ Found {len(paths)} endpoint paths:")
            for path in sorted(paths.keys()):
                methods = list(paths[path].keys())
                print(f"  {path} - {', '.join(methods).upper()}")
            
            # Check specifically for game_setup endpoints
            setup_endpoints = [path for path in paths.keys() if "setup" in path or "invitation" in path]
            if setup_endpoints:
                print(f"\n🎯 Game Setup Endpoints Found:")
                for endpoint in setup_endpoints:
                    print(f"  ✅ {endpoint}")
            else:
                print(f"\n❌ No game setup endpoints found")
                
        else:
            print(f"❌ Failed to get OpenAPI spec: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking endpoints: {e}")

if __name__ == "__main__":
    check_endpoints() 