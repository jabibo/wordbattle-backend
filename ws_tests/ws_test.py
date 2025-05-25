# ws_test.py
import asyncio
import websockets
import json
import sys

async def test_websocket(game_id, token):
    """Test WebSocket connection to a game."""
    uri = f"ws://localhost:8000/ws/games/{game_id}?token={token}"
    print(f"Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            
            # Receive initial game state
            response = await websocket.recv()
            game_state = json.loads(response)
            print(f"Initial game state received: {json.dumps(game_state, indent=2)}")
            
            # Keep listening for updates
            print("\nWaiting for game updates (press Ctrl+C to exit)...")
            while True:
                response = await websocket.recv()
                update = json.loads(response)
                print(f"\nGame update received: {json.dumps(update, indent=2)}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python ws_test.py <game_id> <token>")
        sys.exit(1)
    
    game_id = sys.argv[1]
    token = sys.argv[2]
    
    asyncio.run(test_websocket(game_id, token))
