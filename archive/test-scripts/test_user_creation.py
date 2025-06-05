#!/usr/bin/env python3
"""
Test script to verify test user creation with correct email addresses
"""
import requests
import json

# Test the admin endpoint for creating test users
BACKEND_URL = "http://localhost:8000"  # Change this to your backend URL

def test_user_creation():
    """Test that test users are created with correct email addresses"""
    print("🧪 Testing Test User Creation")
    print("=" * 40)
    
    try:
        # Call the admin endpoint to create test tokens
        response = requests.post(f"{BACKEND_URL}/admin/debug/create-test-tokens", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Test users created successfully!")
            print(f"Message: {data['message']}")
            
            # Check the users
            for user_data in data['users']:
                username = user_data['username']
                email = user_data['email']
                expected_email = f"{username}@binge.de"
                
                print(f"\n👤 User: {username}")
                print(f"   Email: {email}")
                print(f"   Expected: {expected_email}")
                
                if email == expected_email:
                    print("   ✅ Email is correct!")
                else:
                    print("   ❌ Email is incorrect!")
                    
            return True
        else:
            print(f"❌ Failed to create test users: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_user_creation() 