#!/usr/bin/env python3
"""
Test if the connectivity bug fix is deployed to Google Cloud Run.

This script tests the deployed service to see if it has our connectivity fix.
"""

import requests
import json

# The deployed service URL
SERVICE_URL = "https://wordbattle-backend-441752988736.europe-west1.run.app"

def test_deployed_connectivity_fix():
    """Test if the deployed service has our connectivity bug fix."""
    print("=" * 70)
    print("TESTING DEPLOYED SERVICE FOR CONNECTIVITY BUG FIX")
    print("=" * 70)
    
    print(f"Service URL: {SERVICE_URL}")
    
    # First, test if the service is responding
    try:
        health_response = requests.get(f"{SERVICE_URL}/health", timeout=10)
        print(f"Health check: {health_response.status_code}")
        if health_response.status_code == 200:
            print("✅ Service is responding")
        else:
            print("❌ Service health check failed")
            return False
    except Exception as e:
        print(f"❌ Cannot reach service: {e}")
        return False
    
    # Check if we can access the API docs to see available endpoints
    try:
        docs_response = requests.get(f"{SERVICE_URL}/docs", timeout=10)
        print(f"API docs: {docs_response.status_code}")
    except Exception as e:
        print(f"API docs not accessible: {e}")
    
    # Try to get debug tokens to see if we can authenticate
    try:
        debug_response = requests.get(f"{SERVICE_URL}/debug/tokens", timeout=10)
        print(f"Debug tokens: {debug_response.status_code}")
        if debug_response.status_code == 200:
            tokens_data = debug_response.json()
            print("✅ Debug tokens endpoint working")
            
            # Try to use a token to create a game and test the move validation
            if 'tokens' in tokens_data and len(tokens_data['tokens']) > 0:
                token = tokens_data['tokens'][0]['token']
                return test_move_validation_with_token(token)
            else:
                print("❌ No tokens available in debug response")
                return False
        else:
            print("❌ Debug tokens endpoint not working")
            return False
    except Exception as e:
        print(f"❌ Error accessing debug tokens: {e}")
        return False

def test_move_validation_with_token(token):
    """Test move validation using a valid token."""
    print(f"\n" + "=" * 70)
    print("TESTING MOVE VALIDATION WITH CONNECTIVITY FIX")
    print("=" * 70)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Create a game
        game_data = {"language": "en", "max_players": 2}
        create_response = requests.post(f"{SERVICE_URL}/games/", json=game_data, headers=headers, timeout=10)
        
        if create_response.status_code != 200:
            print(f"❌ Failed to create game: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False
        
        game_id = create_response.json()["id"]
        print(f"✅ Created game: {game_id}")
        
        # Start the game (this might require another player, so we'll try)
        start_response = requests.post(f"{SERVICE_URL}/games/{game_id}/start", headers=headers, timeout=10)
        print(f"Start game response: {start_response.status_code}")
        
        # Try to make a move that would test our connectivity fix
        # This is a simplified test - in a real scenario we'd need to set up the board properly
        move_data = [
            {"row": 7, "col": 7, "letter": "C"},  # Center tile
            {"row": 7, "col": 8, "letter": "A"},
            {"row": 7, "col": 9, "letter": "T"}
        ]
        
        move_response = requests.post(f"{SERVICE_URL}/games/{game_id}/move", json=move_data, headers=headers, timeout=10)
        print(f"Move response: {move_response.status_code}")
        
        if move_response.status_code == 200:
            response_data = move_response.json()
            print(f"✅ Move accepted!")
            print(f"Response: {response_data}")
            
            # Check if the response has our enhanced message format
            if 'message' in response_data and 'Valid move!' in response_data.get('message', ''):
                print("✅ Enhanced validation messages are present!")
                print("✅ Connectivity bug fix appears to be DEPLOYED!")
                return True
            else:
                print("⚠️  Move accepted but enhanced messages not detected")
                print("⚠️  May be running older version")
                return False
        else:
            print(f"❌ Move rejected: {move_response.status_code}")
            print(f"Response: {move_response.text}")
            
            # Check if the error message format indicates our fix
            try:
                error_data = move_response.json()
                if 'detail' in error_data and isinstance(error_data['detail'], str):
                    if 'Please place at least one tile' in error_data['detail'] or 'center star square' in error_data['detail']:
                        print("✅ Enhanced error messages detected!")
                        print("✅ Connectivity bug fix appears to be DEPLOYED!")
                        return True
            except:
                pass
            
            return False
            
    except Exception as e:
        print(f"❌ Error testing move validation: {e}")
        return False

def main():
    """Main test function."""
    fix_deployed = test_deployed_connectivity_fix()
    
    print(f"\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    
    if fix_deployed:
        print("🎉 SUCCESS: Connectivity bug fix IS DEPLOYED!")
        print("   The deployed service has our enhanced validation logic.")
    else:
        print("❌ PROBLEM: Connectivity bug fix is NOT DEPLOYED!")
        print("   The deployed service appears to be running an older version.")
        print("   You need to deploy the updated code with our fixes.")
    
    print(f"\nDeployment needed: {'No' if fix_deployed else 'Yes'}")
    
    return 0 if fix_deployed else 1

if __name__ == "__main__":
    exit(main()) 