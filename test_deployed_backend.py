#!/usr/bin/env python3

import requests
import json
import time
import random
import string

# Base URL for the deployed service
BASE_URL = "https://wordbattle-backend-441752988736.europe-west1.run.app"

def generate_test_email():
    """Generate a unique test email address."""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

def test_health_check():
    """Test the health endpoint."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Health: {data.get('status')}")
            print(f"   Database: {data.get('database')}")
            print("   ✅ Health check passed!")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

def test_database_status():
    """Test the database status endpoint."""
    print("\n🔍 Testing database status...")
    try:
        response = requests.get(f"{BASE_URL}/database/status", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', {})
            print(f"   Tables exist: {status.get('tables_exist')}")
            print(f"   Users: {status.get('user_count')}")
            print(f"   Games: {status.get('game_count')}")
            word_counts = status.get('word_counts', {})
            print(f"   German words: {word_counts.get('de', 0)}")
            print(f"   English words: {word_counts.get('en', 0)}")
            print("   ✅ Database status check passed!")
            return True
        else:
            print(f"   ❌ Database status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Database status error: {e}")
        return False

def test_my_invitations_without_auth():
    """Test my-invitations endpoint without authentication."""
    print("\n🔍 Testing /games/my-invitations without authentication...")
    try:
        response = requests.get(f"{BASE_URL}/games/my-invitations", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Correctly returns 401 for unauthenticated request")
            return True
        else:
            print(f"   ❌ Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_user_registration_and_authentication():
    """Test user registration and login flow."""
    print("\n🔍 Testing user registration and authentication...")
    
    # Generate unique credentials
    test_email = generate_test_email()
    username = f"testuser_{int(time.time())}"
    password = "testpass123"
    
    print(f"   Creating user: {username}")
    print(f"   Email: {test_email}")
    
    # Register user
    register_data = {
        "username": username,
        "email": test_email,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/register", json=register_data, timeout=10)
        print(f"   Registration status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ User registered successfully")
        elif response.status_code == 400 and "already exists" in response.text:
            print("   ℹ️  User already exists, continuing...")
        else:
            print(f"   ❌ Registration failed: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return None, None
    
    # Login to get token
    print("   Logging in...")
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/token", data=login_data, timeout=10)
        print(f"   Login status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print("   ✅ Login successful, token obtained")
            return access_token, username
        else:
            print(f"   ❌ Login failed: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return None, None

def test_my_invitations_with_auth(access_token):
    """Test my-invitations endpoint with authentication."""
    print("\n🔍 Testing /games/my-invitations with authentication...")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/games/my-invitations", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Endpoint works correctly with authentication!")
            print(f"   Response structure:")
            print(f"     - invitations: {type(data.get('invitations', []))}")
            print(f"     - total_count: {data.get('total_count', 0)}")
            print(f"     - pending_count: {data.get('pending_count', 0)}")
            
            invitations = data.get('invitations', [])
            print(f"   📝 Found {len(invitations)} invitation(s)")
            
            if invitations:
                print("   📋 First invitation structure:")
                first_inv = invitations[0]
                for key in ['invitation_id', 'game_id', 'inviter', 'game', 'status', 'created_at']:
                    if key in first_inv:
                        print(f"     - {key}: {type(first_inv[key])}")
            
            return True
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_other_endpoints(access_token):
    """Test other key endpoints to ensure they still work."""
    print("\n🔍 Testing other key endpoints...")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    endpoints_to_test = [
        ("/games/my-games", "My Games"),
        ("/users/language", "User Language"),
    ]
    
    for endpoint, name in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {name}: Working ({endpoint})")
            else:
                print(f"   ⚠️  {name}: Status {response.status_code} ({endpoint})")
        except Exception as e:
            print(f"   ❌ {name}: Error {e}")

def test_api_documentation():
    """Test that API documentation is accessible."""
    print("\n🔍 Testing API documentation...")
    
    try:
        # Test OpenAPI schema
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get('paths', {})
            if '/games/my-invitations' in paths:
                print("   ✅ OpenAPI schema includes /games/my-invitations")
            else:
                print("   ❌ OpenAPI schema missing /games/my-invitations")
            
            print(f"   📊 Total API endpoints: {len(paths)}")
            print("   ✅ API documentation accessible")
            return True
        else:
            print(f"   ❌ API documentation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ API documentation error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 WordBattle Backend Deployment Test")
    print("=====================================")
    print(f"Testing deployed service: {BASE_URL}")
    print("")
    
    results = []
    
    # Test 1: Health Check
    results.append(test_health_check())
    
    # Test 2: Database Status  
    results.append(test_database_status())
    
    # Test 3: My Invitations without auth
    results.append(test_my_invitations_without_auth())
    
    # Test 4: User Registration and Authentication
    access_token, username = test_user_registration_and_authentication()
    if access_token:
        results.append(True)
        
        # Test 5: My Invitations with auth
        results.append(test_my_invitations_with_auth(access_token))
        
        # Test 6: Other endpoints
        test_other_endpoints(access_token)
    else:
        results.append(False)
        results.append(False)
    
    # Test 7: API Documentation
    results.append(test_api_documentation())
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "Health Check",
        "Database Status", 
        "My-Invitations (no auth)",
        "User Registration/Login",
        "My-Invitations (with auth)",
        "API Documentation"
    ]
    
    for i, (test_name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ WordBattle backend deployment is working correctly!")
        print("✅ /games/my-invitations endpoint has been successfully fixed!")
        print("\n🔗 Service URL: " + BASE_URL)
        print("📚 API Docs: " + BASE_URL + "/docs")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the logs above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 