from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Map of game_id -> list of connected websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)
        logger.info(f"Client connected to game {game_id}. Total connections: {len(self.active_connections[game_id])}")
    
    def disconnect(self, websocket: WebSocket, game_id: str):
        if game_id in self.active_connections:
            if websocket in self.active_connections[game_id]:
                self.active_connections[game_id].remove(websocket)
                logger.info(f"Client disconnected from game {game_id}. Remaining connections: {len(self.active_connections[game_id])}")
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
                logger.info(f"No more connections for game {game_id}")
    
    async def broadcast(self, game_id: str, message: Any):
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to client: {e}")
            logger.info(f"Broadcast message to {len(self.active_connections[game_id])} clients for game {game_id}")

manager = ConnectionManager()
