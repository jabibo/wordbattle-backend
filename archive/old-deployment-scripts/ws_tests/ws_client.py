import asyncio
import websockets
import json
import sys

async def connect_to_game(game_id, token):
    uri = f"ws://localhost:8000/ws/games/{game_id}?token={token}"
    print(f"Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Receive initial game state
            response = await websocket.recv()
            game_state = json.loads(response)
            print(f"Initial game state: {json.dumps(game_state, indent=2)}")
            
            # Keep listening for updates
            print("Waiting for game updates (press Ctrl+C to exit)...")
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
        print("Usage: python ws_client.py <game_id> <token>")
        sys.exit(1)
    
    game_id = sys.argv[1]
    token = sys.argv[2]
    
    asyncio.run(connect_to_game(game_id, token))
