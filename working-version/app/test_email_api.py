import requests
import json

def test_email_authentication():
    """Test the email authentication API endpoint"""
    
    base_url = "http://localhost:8000"  # Docker container port mapping
    
    print("🧪 Testing Email Authentication API")
    print("=" * 50)
    
    # Test 1: Register a user with email only
    print("\n1. Testing user registration...")
    register_data = {
        "username": "testuser_jan",
        "email": "jan@binge.de"
    }
    
    try:
        response = requests.post(f"{base_url}/users/register-email-only", json=register_data)
        print(f"Registration Status: {response.status_code}")
        print(f"Registration Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Please start the server with: uvicorn app.main:app --reload")
        return
    except Exception as e:
        print(f"Registration Error: {e}")
    
    # Test 2: Request login code
    print("\n2. Testing login code request...")
    login_data = {
        "email": "jan@binge.de",
        "remember_me": True
    }
    
    try:
        response = requests.post(f"{base_url}/auth/email-login", json=login_data)
        print(f"Login Request Status: {response.status_code}")
        print(f"Login Request Response: {response.json()}")
        
        if response.status_code == 200:
            print("\n✅ Email should be sent to jan@binge.de")
            print("📧 Check your email for the 6-digit verification code")
            
            # Prompt for verification code
            verification_code = input("\nEnter the verification code from your email: ")
            
            # Test 3: Verify the code
            print("\n3. Testing code verification...")
            verify_data = {
                "email": "jan@binge.de",
                "verification_code": verification_code,
                "remember_me": True
            }
            
            response = requests.post(f"{base_url}/auth/verify-code", json=verify_data)
            print(f"Verification Status: {response.status_code}")
            print(f"Verification Response: {response.json()}")
            
            if response.status_code == 200:
                print("\n🎉 Email authentication test successful!")
                data = response.json()
                print(f"Access Token: {data.get('access_token', 'N/A')[:50]}...")
                print(f"User: {data.get('user', {})}")
            else:
                print("\n❌ Code verification failed")
        
    except Exception as e:
        print(f"Login Error: {e}")

if __name__ == "__main__":
    test_email_authentication() 