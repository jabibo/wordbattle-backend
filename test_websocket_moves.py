#!/usr/bin/env python3
"""
Test script to verify WebSocket notifications for both human and computer moves.
This will help identify if the issue is specific to computer moves or all moves.
"""

import asyncio
import websockets
import requests
import json
import sys
from datetime import datetime

# Test environment URL - Updated to match deployment output
BASE_URL = "https://wordbattle-backend-test-441752988736.europe-west1.run.app"
WS_URL = "wss://wordbattle-backend-test-441752988736.europe-west1.run.app"

async def test_websocket_notifications():
    """Test WebSocket notifications for both human and computer moves."""
    
    print("🔍 Testing WebSocket Move Notifications")
    print("=" * 60)
    
    # Step 1: Login as admin
    print("🔧 Step 1: Admin login")
    admin_response = requests.post(f"{BASE_URL}/auth/simple-admin-login", params={
        "email": "test@example.com"
    })
    
    if admin_response.status_code != 200:
        print(f"❌ Admin login failed: {admin_response.status_code}")
        return False
    
    admin_data = admin_response.json()
    admin_token = admin_data["access_token"]
    print("✅ Admin login successful")
    
    # Step 2: Create a new game with computer player
    print("🎮 Step 2: Creating new game with computer player")
    game_response = requests.post(f"{BASE_URL}/games/", 
        json={
            "language": "en",
            "max_players": 2,
            "add_computer_player": True,
            "computer_difficulty": "medium"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if game_response.status_code not in [200, 201]:
        print(f"❌ Game creation failed: {game_response.status_code}")
        print(f"Response: {game_response.text}")
        return False
    
    game_data = game_response.json()
    game_id = game_data["id"]
    print(f"✅ Game created: {game_id}")
    
    # Step 3: Connect to WebSocket
    print("🔌 Step 3: Connecting to WebSocket")
    websocket_messages = []
    
    try:
        ws_uri = f"{WS_URL}/ws/games/{game_id}?token={admin_token}"
        print(f"Connecting to: {ws_uri}")
        
        async with websockets.connect(ws_uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Step 4: Test human move (pass)
            print("👤 Step 4: Testing human move WebSocket notification")
            
            # Make a human pass move
            pass_response = requests.post(f"{BASE_URL}/games/{game_id}/pass",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if pass_response.status_code != 200:
                print(f"❌ Human pass failed: {pass_response.status_code}")
                return False
            
            print("✅ Human pass move made")
            
            # Wait for WebSocket message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                msg_data = json.loads(message)
                websocket_messages.append(msg_data)
                print(f"✅ Received WebSocket message for human move: {msg_data.get('type', 'unknown')}")
                
                if msg_data.get('type') == 'game_update':
                    print("  📡 Human move triggered 'game_update' WebSocket notification")
                else:
                    print(f"  📡 Human move triggered '{msg_data.get('type')}' WebSocket notification")
                    
            except asyncio.TimeoutError:
                print("❌ No WebSocket message received for human move")
            
            # Step 5: Test computer move
            print("🤖 Step 5: Testing computer move WebSocket notification")
            
            computer_move_response = requests.post(f"{BASE_URL}/games/{game_id}/computer-move",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if computer_move_response.status_code != 200:
                print(f"❌ Computer move failed: {computer_move_response.status_code}")
                print(f"Response: {computer_move_response.text}")
                return False
            
            computer_move_data = computer_move_response.json()
            print("✅ Computer move made")
            print(f"  Move: {computer_move_data.get('move', {}).get('type', 'unknown')}")
            
            # Wait for WebSocket message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                msg_data = json.loads(message)
                websocket_messages.append(msg_data)
                print(f"✅ Received WebSocket message for computer move: {msg_data.get('type', 'unknown')}")
                
                if msg_data.get('type') == 'computer_move':
                    print("  📡 Computer move triggered 'computer_move' WebSocket notification")
                elif msg_data.get('type') == 'game_update':
                    print("  📡 Computer move triggered 'game_update' WebSocket notification")
                else:
                    print(f"  📡 Computer move triggered '{msg_data.get('type')}' WebSocket notification")
                    
            except asyncio.TimeoutError:
                print("❌ No WebSocket message received for computer move")
            
            # Try to receive any additional messages
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    msg_data = json.loads(message)
                    websocket_messages.append(msg_data)
                    print(f"✅ Additional message: {msg_data.get('type', 'unknown')}")
            except asyncio.TimeoutError:
                print("⏰ No more messages")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False
    
    # Step 6: Analyze results
    print("📊 Step 6: Analyzing WebSocket notifications")
    
    human_move_notifications = [msg for msg in websocket_messages if msg.get('type') in ['game_update', 'move_made']]
    computer_move_notifications = [msg for msg in websocket_messages if msg.get('type') == 'computer_move']
    
    print(f"\n📈 Results:")
    print(f"  Total WebSocket messages received: {len(websocket_messages)}")
    print(f"  Human move notifications: {len(human_move_notifications)}")
    print(f"  Computer move notifications: {len(computer_move_notifications)}")
    
    print(f"\n📋 All messages received:")
    for i, msg in enumerate(websocket_messages):
        print(f"  {i+1}. Type: {msg.get('type', 'unknown')}")
        if msg.get('type') == 'computer_move':
            print(f"     Move: {msg.get('move', {}).get('type', 'unknown')}")
            print(f"     Next player: {msg.get('next_player_id')}")
    
    # Determine success
    websocket_working = len(websocket_messages) > 0
    human_notifications_working = len(human_move_notifications) > 0
    computer_notifications_working = len(computer_move_notifications) > 0
    
    print(f"\n🎯 Analysis:")
    print(f"  WebSocket connection: {'✅ Working' if websocket_working else '❌ Failed'}")
    print(f"  Human move notifications: {'✅ Working' if human_notifications_working else '❌ Not working'}")
    print(f"  Computer move notifications: {'✅ Working' if computer_notifications_working else '❌ Not working'}")
    
    if websocket_working and not computer_notifications_working:
        print(f"\n🔍 Issue identified: WebSocket works for human moves but NOT for computer moves")
        print(f"  This suggests the computer move broadcast code is not being executed")
    elif websocket_working and computer_notifications_working:
        print(f"\n✅ All WebSocket notifications are working correctly!")
    elif not websocket_working:
        print(f"\n❌ WebSocket connection is not working at all")
    
    return websocket_working and computer_notifications_working

def main():
    """Run the WebSocket move notification test."""
    
    print(f"🚀 WebSocket Move Notification Test")
    print(f"Target: {BASE_URL}")
    print(f"WebSocket: {WS_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    success = asyncio.run(test_websocket_notifications())
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 WebSocket computer move notifications are WORKING!")
    else:
        print("❌ WebSocket computer move notifications are NOT working!")
        print("🔧 Check the analysis above for specific issues")

if __name__ == "__main__":
    main() 