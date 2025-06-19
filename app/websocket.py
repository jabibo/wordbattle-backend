from fastapi import WebSocket
from typing import Dict, Set, List, Any, Optional, Tuple
import json
import logging
from datetime import datetime, timezone
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


class UserNotificationManager:
    """WebSocket manager for user notification connections (invitations, etc.)"""
    
    def __init__(self):
        # Dictionary to store active notification connections per user
        self.user_connections: Dict[int, WebSocket] = {}  # user_id -> websocket
        # Dictionary to store user info per connection
        self.connection_users: Dict[WebSocket, User] = {}  # websocket -> user
    
    async def connect(self, websocket: WebSocket, user: User):
        """Connect a user's notification WebSocket."""
        # Close existing connection if user already connected
        if user.id in self.user_connections:
            old_websocket = self.user_connections[user.id]
            logger.info(f"User {user.username} already has notification connection, closing old one")
            try:
                await old_websocket.close(code=4000)
            except:
                pass
            self.disconnect(old_websocket)
        
        # Store new connection
        self.user_connections[user.id] = websocket
        self.connection_users[websocket] = user
        
        # Send connection established message
        await self.send_to_user(user.id, {
            "type": "connection_established",
            "user_id": user.id,
            "username": user.username,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"User notification connection established: {user.username} (ID: {user.id})")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a user's notification WebSocket."""
        try:
            if websocket in self.connection_users:
                user = self.connection_users[websocket]
                del self.connection_users[websocket]
                
                # Remove from user_connections if it matches
                if user.id in self.user_connections and self.user_connections[user.id] == websocket:
                    del self.user_connections[user.id]
                
                logger.info(f"User notification connection closed: {user.username} (ID: {user.id})")
        except Exception as e:
            logger.error(f"Error during notification disconnect: {e}")
    
    async def send_to_user(self, user_id: int, message: dict):
        """Send a notification message to a specific user."""
        if user_id in self.user_connections:
            websocket = self.user_connections[user_id]
            try:
                await websocket.send_json(message)
                logger.debug(f"Notification sent to user {user_id}: {message['type']}")
            except Exception as e:
                logger.error(f"Error sending notification to user {user_id}: {e}")
                # Clean up broken connection
                self.disconnect(websocket)
                return False
        else:
            logger.debug(f"User {user_id} not connected for notifications")
            return False
        return True
    
    async def send_invitation_received(self, user_id: int, invitation_data: dict):
        """Send invitation_received notification to user."""
        message = {
            "type": "invitation_received",
            "invitation": invitation_data
        }
        await self.send_to_user(user_id, message)
    
    async def send_invitation_status_changed(self, user_id: int, invitation_id: int, 
                                           new_status: str, game_id: str):
        """Send invitation status change notification."""
        message = {
            "type": "invitation_status_changed",
            "invitation_id": invitation_id,
            "new_status": new_status,
            "game_id": game_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.send_to_user(user_id, message)
    
    async def send_invitation_cancelled(self, user_id: int, invitation_id: int, 
                                      game_id: str, cancelled_by: str, reason: str):
        """Send invitation cancelled notification."""
        message = {
            "type": "invitation_cancelled",
            "invitation_id": invitation_id,
            "game_id": game_id,
            "cancelled_by": cancelled_by,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.send_to_user(user_id, message)
    
    async def send_game_started(self, user_id: int, game_id: str, invitation_id: int, 
                              inviter_username: str):
        """Send game started notification."""
        message = {
            "type": "game_started",
            "game_id": game_id,
            "invitation_id": invitation_id,
            "game_url": f"/games/{game_id}",
            "message": f"Your game with {inviter_username} has started!",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.send_to_user(user_id, message)
    
    def is_user_connected(self, user_id: int) -> bool:
        """Check if a user has an active notification connection."""
        return user_id in self.user_connections
    
    def get_connected_user_count(self) -> int:
        """Get the number of users connected for notifications."""
        return len(self.user_connections)


# Global instances
manager = ConnectionManager()
notification_manager = UserNotificationManager()
