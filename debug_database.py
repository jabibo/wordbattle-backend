#!/usr/bin/env python3
"""
Debug script to check database state and test token creation
"""
import requests
import json

BASE_URL = "https://wordbattle-backend-prod-skhco4fxoq-ew.a.run.app"

def test_email_login_flow():
    """Test the complete email login flow to see where it breaks."""
    
    email = "jan@binge.de"
    
    print("🔍 Testing complete email login flow...")
    print(f"📧 Email: {email}")
    
    # Step 1: Request email login
    print("\n1️⃣ Requesting email login...")
    url = f"{BASE_URL}/auth/email-login"
    payload = {
        "email": email,
        "remember_me": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"📥 Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Email login request successful")
            print(f"📥 Response: {json.dumps(response.json(), indent=2)}")
        else:
            print("❌ Email login request failed")
            print(f"📥 Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return
    
    # Step 2: Check database state
    print("\n2️⃣ Checking database state...")
    debug_url = f"{BASE_URL}/admin/debug/persistent-tokens"
    
    try:
        response = requests.get(debug_url, timeout=30)
        print(f"📥 Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Users with tokens: {len(data.get('users_with_tokens', []))}")
            print(f"📊 Total users: {data.get('total_users', 0)}")
            
            if data.get('users_with_tokens'):
                print("🔍 Users with persistent tokens:")
                for user in data['users_with_tokens']:
                    print(f"  - {user}")
        else:
            print("❌ Debug request failed")
            print(f"📥 Response: {response.text}")
    except Exception as e:
        print(f"❌ Debug request failed: {e}")
    
    print("\n💡 Next steps:")
    print("1. Check your email for verification code")
    print("2. Use the verification code to complete login")
    print("3. Check if persistent token gets saved")

def test_database_users():
    """Check what users are in the database."""
    
    print("\n🔍 Checking database users...")
    
    # Use the admin endpoint to check users
    url = f"{BASE_URL}/admin/users"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json()
            print(f"📊 Total users: {len(users)}")
            
            for user in users:
                print(f"👤 User: {user.get('username')} ({user.get('email')})")
                print(f"   - ID: {user.get('id')}")
                print(f"   - Verified: {user.get('is_email_verified')}")
                print(f"   - Last login: {user.get('last_login')}")
                print()
        else:
            print("❌ Failed to get users")
            print(f"📥 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🧪 WordBattle Database Debug Test")
    print("=" * 50)
    
    test_database_users()
    test_email_login_flow()
    
    print("\n" + "=" * 50)
    print("�� Test completed") 