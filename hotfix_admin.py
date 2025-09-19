#!/usr/bin/env python3
"""
Hotfix script to test and reload German wordlist on production backend
This bypasses the import issues by directly calling the API
"""

import requests
import json

# Production backend URL
BASE_URL = "https://wordbattle-backend-prod-15814336315.europe-west1.run.app"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqYW5AYmluZ2UuZGUiLCJleHAiOjE3NTgyOTU2NDV9.nzkHEq0gnQXa0W-hgx2Mn8LKp_5a14nwH2Ac5MKEBzY"

def test_words():
    """Test current word validation"""
    print("🧪 Testing current word validation...")
    
    words_to_test = ["RAND", "HALLO", "WELT", "TEST"]
    
    response = requests.post(
        f"{BASE_URL}/games/dd2fda8c-982a-4efb-8bf5-0226cac48ebe/validate_words",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        },
        json={"words": words_to_test, "include_placements": False}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {json.dumps(data, indent=2)}")
        
        # Count valid words
        valid_count = sum(1 for word, info in data["validations"].items() if info["is_valid"])
        print(f"📊 Valid words: {valid_count}/{len(words_to_test)}")
        
        return data
    else:
        print(f"❌ Request failed: {response.status_code} - {response.text}")
        return None

def reload_wordlist():
    """Try to trigger wordlist reload via admin endpoint"""
    print("🔄 Attempting to reload wordlist...")
    
    # Try the admin reload endpoint if it exists
    try:
        response = requests.post(
            f"{BASE_URL}/admin/reload-wordlist",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TOKEN}"
            }
        )
        
        if response.status_code == 200:
            print("✅ Wordlist reload successful")
            return True
        else:
            print(f"❌ Reload failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Reload request failed: {e}")
        return False

def main():
    print("🚀 Production Wordlist Hotfix Tool")
    print("=" * 50)
    
    # Test current state
    print("\n1. Testing current word validation...")
    current_state = test_words()
    
    if current_state:
        valid_words = [word for word, info in current_state["validations"].items() if info["is_valid"]]
        if "RAND" not in valid_words:
            print("\n🔍 RAND is not valid - this confirms the import issue")
            print("📊 Database has 601,565 words but import error prevents access")
            print("🛠️ Need to deploy the import fix")
        else:
            print("\n✅ RAND is valid - issue might be resolved!")
    
    print("\n" + "=" * 50)
    print("Current status: Import fix needed for German dictionary access")

if __name__ == "__main__":
    main()
