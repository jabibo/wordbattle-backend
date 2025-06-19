from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from starlette.websockets import WebSocketState
from app.websocket import manager, notification_manager
from app.auth import get_user_from_token
from app.models import Game, Player, User
from app.db import get_db
from sqlalchemy.orm import Session
from jose import JWTError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/games/{game_id}/ws")
async def websocket_game_endpoint(
    websocket: WebSocket,
    game_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for game-specific connections."""
    try:
        # Validate token and get user
        user = get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001)
            return

        # Check if user is part of the game
        player = db.query(Player).filter(
            Player.game_id == game_id,
            Player.user_id == user.id
        ).first()
        
        if not player:
            await websocket.close(code=4003)
            return

        # Accept connection and connect to manager
        await websocket.accept()
        await manager.connect(websocket, game_id, user)
        
        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                # Handle any client messages if needed
                logger.debug(f"Received message from {user.username} in game {game_id}: {data}")
        except WebSocketDisconnect:
            manager.disconnect(websocket, game_id)
    except JWTError:
        await websocket.close(code=4001)
    except Exception as e:
        logger.error(f"WebSocket error in game {game_id}: {e}")
        try:
            await websocket.close(code=4000)
        except:
            pass
        manager.disconnect(websocket, game_id)


@router.websocket("/ws/user/notifications")
async def websocket_user_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication")
):
    """
    WebSocket endpoint for user notifications (invitations, etc.)
    
    Connection URL: ws://localhost:8000/ws/user/notifications?token=your_jwt_token
    Production URL: wss://your-server/ws/user/notifications?token=your_jwt_token
    """
    try:
        # Get database session manually since we can't use Depends in WebSocket
        from app.db import SessionLocal
        db = SessionLocal()
        
        try:
            # Validate token and get user
            user = get_user_from_token(token, db)
            if not user:
                logger.warning("WebSocket notification connection rejected: Invalid token")
                await websocket.close(code=4001)
                return

            # Accept connection
            await websocket.accept()
            
            # Connect to notification manager
            await notification_manager.connect(websocket, user)
            
            logger.info(f"User {user.username} connected to notification WebSocket")
            
            try:
                # Keep connection alive and handle any incoming messages
                while True:
                    try:
                        # Receive messages from client (heartbeat, etc.)
                        data = await websocket.receive_text()
                        
                        # Handle ping/pong for connection health
                        if data == "ping":
                            await websocket.send_text("pong")
                            logger.debug(f"Ping/pong with user {user.username}")
                        else:
                            logger.debug(f"Received notification message from {user.username}: {data}")
                            
                    except WebSocketDisconnect:
                        logger.info(f"User {user.username} disconnected from notifications")
                        break
                        
            except Exception as e:
                logger.error(f"Error in notification WebSocket for user {user.username}: {e}")
                
        finally:
            # Clean up connection
            notification_manager.disconnect(websocket)
            db.close()
            
    except JWTError:
        logger.warning("WebSocket notification connection rejected: JWT error")
        await websocket.close(code=4001)
    except Exception as e:
        logger.error(f"WebSocket notification error: {e}")
        try:
            await websocket.close(code=4000)
        except:
            pass 