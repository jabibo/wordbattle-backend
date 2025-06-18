#!/usr/bin/env python3
"""
Test script to debug persistent token authentication issue.
This simulates what the Flutter app is doing.
"""
import requests
import json

BASE_URL = "https://wordbattle-backend-prod-skhco4fxoq-ew.a.run.app"

def test_persistent_token():
    """Test the persistent token that should be working."""
    
    # This is the token we saw in the Flutter debug logs
    persistent_token = "Cj3JZa_P737LyF8sz3sMDOF4I06oaR0sFuTsawYB7Hc"
    
    print(f"🔍 Testing persistent token: {persistent_token}")
    
    # Test the persistent-login endpoint
    url = f"{BASE_URL}/auth/persistent-login"
    payload = {
        "persistent_token": persistent_token
    }
    
    print(f"📤 Making request to: {url}")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            print(f"📥 Response: {json.dumps(response.json(), indent=2)}")
        else:
            print("❌ FAILED!")
            try:
                error_data = response.json()
                print(f"📥 Error Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📥 Raw Response: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_admin_debug_endpoint():
    """Test the admin debug endpoint to see persistent token status."""
    
    url = f"{BASE_URL}/admin/debug/persistent-tokens"
    
    print(f"\n🔍 Testing admin debug endpoint: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            print(f"📥 Response: {json.dumps(response.json(), indent=2)}")
        else:
            print("❌ FAILED!")
            try:
                error_data = response.json()
                print(f"📥 Error Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📥 Raw Response: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🧪 WordBattle Persistent Token Debug Test")
    print("=" * 50)
    
    test_persistent_token()
    test_admin_debug_endpoint()
    
    print("\n" + "=" * 50)
    print("�� Test completed") 