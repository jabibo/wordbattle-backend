#!/usr/bin/env python3
"""
Script to create missing database tables
"""
import requests

BACKEND_URL = "https://mnirejmq3g.eu-central-1.awsapprunner.com"

def create_missing_tables():
    """Try to create missing tables via API"""
    print("🔧 Creating Missing Database Tables")
    print("=" * 40)
    
    # We'll use the admin endpoint to import wordlists, which should trigger table creation
    # First, let's check what endpoints are available
    
    try:
        response = requests.get(f"{BACKEND_URL}/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            
            print("Available endpoints:")
            for path in sorted(paths.keys()):
                methods = list(paths[path].keys())
                print(f"  {path} - {', '.join(methods).upper()}")
            
            # Check if there's an admin endpoint we can use
            admin_endpoints = [p for p in paths.keys() if "admin" in p]
            print(f"\nAdmin endpoints: {admin_endpoints}")
            
        else:
            print(f"Failed to get OpenAPI spec: {response.status_code}")
            
    except Exception as e:
        print(f"Error checking endpoints: {e}")

if __name__ == "__main__":
    create_missing_tables() 