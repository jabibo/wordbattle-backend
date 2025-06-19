#!/usr/bin/env python3
"""
WebSocket Timeout Fix Verification Test
Tests that WebSocket connections now stay alive longer than 5 minutes
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

# Test configuration
TEST_URL = "wss://wordbattle-backend-test-skhco4fxoq-ew.a.run.app/ws/user/notifications"
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqYW5AYmluZ2UuZGUiLCJleHAiOjE3NTAzNDY2Mzh9.M1t8kXKKW0Uh7_oXh5MnNpGFdA1Lh_TJv-1Xj9wAH8s"  # Replace with valid token

async def test_websocket_longevity():
    """Test WebSocket connection stability over extended period"""
    
    connection_url = f"{TEST_URL}?token={TEST_TOKEN}"
    print(f"🔗 Connecting to: {connection_url}")
    
    try:
        async with websockets.connect(connection_url) as websocket:
            print(f"✅ Connected at {datetime.now()}")
            
            # Wait for connection_established message
            initial_message = await websocket.recv()
            initial_data = json.loads(initial_message)
            print(f"📨 Initial message: {initial_data}")
            
            if initial_data.get("type") == "connection_established":
                print(f"🎉 Connection established for user: {initial_data.get('username')}")
            
            # Test connection over extended period
            start_time = time.time()
            ping_interval = 45  # Match frontend ping interval
            
            print(f"⏱️  Starting longevity test (ping every {ping_interval}s)")
            print("   Target: Stay connected > 5 minutes (300s)")
            print("   With fix: Should stay connected up to 60 minutes")
            
            while True:
                try:
                    # Send ping every 45 seconds
                    await websocket.send("ping")
                    print(f"🏓 Ping sent at {datetime.now()}")
                    
                    # Wait for pong response
                    pong_response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    print(f"🏓 Pong received: {pong_response}")
                    
                    # Calculate elapsed time
                    elapsed = time.time() - start_time
                    minutes = elapsed / 60
                    
                    print(f"⏰ Connection alive for {minutes:.1f} minutes")
                    
                    if elapsed > 300:  # 5 minutes
                        print(f"🎉 SUCCESS: Connection survived past 5 minutes!")
                        print(f"   Previous issue: Connections died at ~5 minutes")
                        print(f"   Current status: Connection stable at {minutes:.1f} minutes")
                    
                    if elapsed > 600:  # 10 minutes - good test duration
                        print(f"🏆 EXCELLENT: Connection stable for {minutes:.1f} minutes")
                        print("   WebSocket timeout fix is working!")
                        break
                    
                    # Wait before next ping
                    await asyncio.sleep(ping_interval)
                    
                except asyncio.TimeoutError:
                    print("❌ Timeout waiting for pong response")
                    break
                except websockets.exceptions.ConnectionClosed:
                    elapsed = time.time() - start_time
                    print(f"❌ Connection closed after {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
                    if elapsed < 300:
                        print("   This indicates the timeout fix may not be working")
                    else:
                        print("   Connection lasted longer than the previous 5-minute limit")
                    break
                    
    except Exception as e:
        print(f"❌ Connection failed: {e}")

async def quick_connection_test():
    """Quick test to verify basic WebSocket functionality"""
    
    connection_url = f"{TEST_URL}?token={TEST_TOKEN}"
    print(f"🔗 Quick connection test: {connection_url}")
    
    try:
        async with websockets.connect(connection_url) as websocket:
            print(f"✅ Connected successfully")
            
            # Wait for initial message
            initial_message = await asyncio.wait_for(websocket.recv(), timeout=10)
            initial_data = json.loads(initial_message)
            print(f"📨 Received: {initial_data}")
            
            # Test ping/pong
            await websocket.send("ping")
            pong_response = await asyncio.wait_for(websocket.recv(), timeout=10)
            print(f"🏓 Ping/pong test: {pong_response}")
            
            print("✅ Basic WebSocket functionality working")
            
    except Exception as e:
        print(f"❌ Quick test failed: {e}")

if __name__ == "__main__":
    print("🧪 WebSocket Timeout Fix Verification")
    print("=====================================")
    
    # First run quick test
    print("\n1️⃣ Running quick connection test...")
    asyncio.run(quick_connection_test())
    
    print("\n2️⃣ Running longevity test...")
    print("   Note: This test will run for up to 10 minutes")
    print("   Press Ctrl+C to stop early")
    
    try:
        asyncio.run(test_websocket_longevity())
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    print("\n✅ Test completed") 