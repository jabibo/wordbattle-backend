#!/usr/bin/env python3
"""
Test script to verify JWT token validation after SECRET_KEY fix
"""
import requests
import jwt
import uuid
from datetime import datetime, timedelta

# The SECRET_KEY that both frontend and backend should now be using
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
BACKEND_URL = "https://mnirejmq3g.eu-central-1.awsapprunner.com"

def create_test_token(email):
    """Create a test JWT token using the same SECRET_KEY as the backend"""
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def register_test_user():
    """Register a test user and get a valid token"""
    print("👤 Registering Test User")
    print("=" * 30)
    
    # Generate unique username and email
    unique_id = uuid.uuid4().hex[:8]
    username = f"testuser_{unique_id}"
    email = f"test_{unique_id}@example.com"
    password = "testpassword123"
    
    print(f"📝 Username: {username}")
    print(f"📧 Email: {email}")
    
    # Register user
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/users/register", 
                               json=register_data, 
                               timeout=10)
        print(f"📡 Registration Status: {response.status_code}")
        print(f"📄 Registration Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ User registered successfully!")
            return username, email, password  # Return username too
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            return None, None, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to register user: {e}")
        return None, None, None

def get_auth_token(username, password):
    """Get authentication token using username/password"""
    print("\n🔑 Getting Authentication Token")
    print("=" * 35)
    
    print(f"🔑 Using username: {username}")
    
    auth_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/token", 
                               data=auth_data,  # Note: using data, not json for form data
                               timeout=10)
        print(f"📡 Auth Status: {response.status_code}")
        print(f"📄 Auth Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"✅ Got auth token: {token[:50]}...")
            return token
        else:
            print(f"❌ Authentication failed with status {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to get auth token: {e}")
        return None

def test_token_validation(token):
    """Test if the backend accepts our JWT token"""
    print("\n🔧 Testing JWT Token Validation")
    print("=" * 40)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try to access the /me endpoint (should be protected)
    try:
        response = requests.get(f"{BACKEND_URL}/me", headers=headers, timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        print(f"📄 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("🎉 SUCCESS: JWT token validation is working!")
            return True
        elif response.status_code == 401:
            print("❌ FAILED: Backend still rejecting valid tokens")
            return False
        else:
            print(f"⚠️  UNEXPECTED: Got status code {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to connect to backend: {e}")
        return False

def test_games_endpoint(token):
    """Test creating a game with the JWT token"""
    print("\n🎮 Testing Games Endpoint")
    print("=" * 30)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    game_data = {
        "language": "en",
        "max_players": 2
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/games/", 
                               headers=headers, 
                               json=game_data, 
                               timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        print(f"📄 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("🎉 SUCCESS: Game creation endpoint working!")
            return True
        else:
            print(f"❌ FAILED: Game creation failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to connect to backend: {e}")
        return False

def test_manual_jwt_token(email):
    """Test manually created JWT token with the same SECRET_KEY"""
    print("\n🔧 Testing Manual JWT Token")
    print("=" * 35)
    
    # Create token manually using the same SECRET_KEY
    manual_token = create_test_token(email)
    print(f"🔑 Manual token: {manual_token[:50]}...")
    
    headers = {
        "Authorization": f"Bearer {manual_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BACKEND_URL}/me", headers=headers, timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        print(f"📄 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("🎉 SUCCESS: Manual JWT token validation working!")
            return True
        else:
            print(f"❌ FAILED: Manual JWT token rejected")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to test manual token: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Comprehensive JWT Validation Test")
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print(f"🔑 Using SECRET_KEY: {SECRET_KEY[:20]}...")
    print()
    
    # Step 1: Register a test user
    username, email, password = register_test_user()
    if not username or not email or not password:
        print("❌ Cannot proceed without a registered user")
        exit(1)
    
    # Step 2: Get official auth token
    auth_token = get_auth_token(username, password)
    if not auth_token:
        print("❌ Cannot proceed without an auth token")
        exit(1)
    
    # Step 3: Test official token validation
    me_test_passed = test_token_validation(auth_token)
    
    # Step 4: Test games endpoint with official token
    games_test_passed = test_games_endpoint(auth_token)
    
    # Step 5: Test manually created token (this tests SECRET_KEY compatibility)
    manual_test_passed = test_manual_jwt_token(email)
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"   User Registration: ✅ PASS")
    print(f"   Token Authentication: ✅ PASS")
    print(f"   /me endpoint (official token): {'✅ PASS' if me_test_passed else '❌ FAIL'}")
    print(f"   /games/ endpoint (official token): {'✅ PASS' if games_test_passed else '❌ FAIL'}")
    print(f"   /me endpoint (manual token): {'✅ PASS' if manual_test_passed else '❌ FAIL'}")
    
    if me_test_passed and games_test_passed and manual_test_passed:
        print("\n🎉 ALL TESTS PASSED! JWT validation is working correctly.")
        print("✅ The SECRET_KEY fix has resolved the authentication issue!")
    else:
        print("\n⚠️  Some tests failed, but basic authentication is working.")
        if manual_test_passed:
            print("✅ Manual JWT tokens work - SECRET_KEY is correctly synchronized!")
        else:
            print("❌ Manual JWT tokens still fail - SECRET_KEY issue may persist.") 