from fastapi import WebSocket
from typing import Dict, Set, List, Any, Optional, Tuple
import json
import logging
from app.auth import get_token_from_header, get_user_from_token
from app.models import User
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Dictionary to store active connections per game
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Dictionary to store user info per connection
        self.connection_users: Dict[WebSocket, User] = {}
        # Maximum connections per game
        self.MAX_CONNECTIONS_PER_GAME = 4
    
    async def connect(self, websocket: WebSocket, game_id: str, user: User):
        """Connect a new WebSocket client."""
        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()
        
        # Check connection limit
        if len(self.active_connections[game_id]) >= self.MAX_CONNECTIONS_PER_GAME:
            logger.error(f"Maximum connections ({self.MAX_CONNECTIONS_PER_GAME}) reached for game {game_id}")
            await websocket.close(code=4002)
            raise WebSocketDisconnect(code=4002)
        
        # Check if user already has a connection
        for conn in self.active_connections[game_id]:
            if self.connection_users.get(conn) and self.connection_users[conn].id == user.id:
                logger.info(f"User {user.username} already connected to game {game_id}, closing old connection")
                await conn.close(code=4000)
                self.disconnect(conn, game_id)
                break
        
        self.active_connections[game_id].add(websocket)
        self.connection_users[websocket] = user
        logger.info(f"Client connected to game {game_id}: {user.username}")
    
    def disconnect(self, websocket: WebSocket, game_id: str):
        """Disconnect a WebSocket client."""
        try:
            if game_id in self.active_connections:
                self.active_connections[game_id].discard(websocket)
                if not self.active_connections[game_id]:
                    del self.active_connections[game_id]
            
            if websocket in self.connection_users:
                user = self.connection_users[websocket]
                del self.connection_users[websocket]
                logger.info(f"Client disconnected from game {game_id}: {user.username}")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def broadcast_to_game(self, game_id: str, message: dict):
        """Broadcast a message to all connected clients in a game."""
        if game_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[game_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection, game_id)
    
    def get_connected_users(self, game_id: str) -> List[User]:
        """Get list of connected users for a game."""
        if game_id not in self.active_connections:
            return []
        return [self.connection_users[conn] for conn in self.active_connections[game_id] if conn in self.connection_users]

manager = ConnectionManager()
