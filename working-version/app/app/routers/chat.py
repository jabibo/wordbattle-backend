from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Game, ChatMessage, Player
from app.auth import get_current_user
from typing import List
from datetime import datetime, timezone
from pydantic import BaseModel

router = APIRouter(prefix="/games", tags=["chat"])

class ChatMessageResponse(BaseModel):
    id: int
    game_id: str
    sender_id: int
    sender_username: str
    message: str
    timestamp: datetime

@router.get("/{game_id}/messages")
def get_chat_messages(
    game_id: str,
    limit: int = 50,
    before_id: int = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get chat messages for a specific game.
    Messages are returned in reverse chronological order (newest first).
    Supports pagination using before_id parameter.
    """
    # Check if game exists and user is part of it
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Game not found")
    
    is_player = db.query(Player).filter_by(game_id=game_id, user_id=current_user.id).first()
    if not is_player and game.creator_id != current_user.id:
        raise HTTPException(403, "You are not part of this game")
    
    # Build query
    query = db.query(ChatMessage).filter(ChatMessage.game_id == game_id)
    
    if before_id:
        query = query.filter(ChatMessage.id < before_id)
    
    # Get messages ordered by timestamp descending, with limit
    messages = query.order_by(ChatMessage.timestamp.desc()).limit(limit).all()
    
    return [
        ChatMessageResponse(
            id=msg.id,
            game_id=msg.game_id,
            sender_id=msg.sender_id,
            sender_username=msg.sender.username,
            message=msg.message,
            timestamp=msg.timestamp
        )
        for msg in messages
    ] 