from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db import get_db
from app.models import Game, GameInvitation, User, Player
from app.models.game import GameStatus
from app.models.game_invitation import InvitationStatus
from app.auth import get_current_user
from app.game_logic.game_state import GameState, GamePhase
from app.routers.games import GameStateEncoder
from app.utils.wordlist_utils import ensure_wordlist_available
from datetime import datetime, timezone, timedelta
import uuid
import json
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/game-setup", tags=["game_setup"])

class GameSetup(BaseModel):
    max_players: int = 2
    language: str = "de"
    invitees: List[str]  # List of usernames to invite

class InvitationResponse(BaseModel):
    game_id: str
    response: bool  # True for accept, False for decline

@router.post("/setup")
def setup_game(
    setup_data: GameSetup,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Setup a new game and send invitations."""
    # Validate max players
    if not (2 <= setup_data.max_players <= 4):
        raise HTTPException(400, "Number of players must be between 2 and 4")
    
    # Validate language and ensure wordlist is available
    if not ensure_wordlist_available(setup_data.language, db):
        raise HTTPException(400, f"Language '{setup_data.language}' not available")
    
    # Create new game
    game_id = str(uuid.uuid4())
    
    # Initialize game state
    game_state = GameState(language=setup_data.language)
    state_data = {
        "board": game_state.board,
        "phase": GamePhase.NOT_STARTED.value,
        "language": setup_data.language
    }
    
    # Create game record
    game = Game(
        id=game_id,
        creator_id=current_user.id,
        current_player_id=current_user.id,
        state=json.dumps(state_data, cls=GameStateEncoder),
        status=GameStatus.SETUP,
        language=setup_data.language,
        max_players=setup_data.max_players,
        created_at=datetime.now(timezone.utc)
    )
    db.add(game)
    
    # Create invitations
    invitations = []
    for username in setup_data.invitees:
        invitee = db.query(User).filter(User.username == username).first()
        if not invitee:
            continue  # Skip invalid usernames
            
        invitation = GameInvitation(
            game_id=game_id,
            inviter_id=current_user.id,
            invitee_id=invitee.id
        )
        invitations.append(invitation)
    
    if not invitations:
        db.rollback()
        raise HTTPException(400, "No valid invitees provided")
    
    db.add_all(invitations)
    
    # Add creator as first player
    player = Player(game_id=game_id, user_id=current_user.id)
    db.add(player)
    
    db.commit()
    
    return {
        "game_id": game_id,
        "invitations_sent": len(invitations)
    }

@router.get("/invitations")
def get_invitations(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all pending invitations for the current user."""
    invitations = db.query(GameInvitation).filter(
        and_(
            GameInvitation.invitee_id == current_user.id,
            GameInvitation.status == InvitationStatus.PENDING
        )
    ).all()
    
    return [{
        "invitation_id": inv.id,
        "game_id": inv.game_id,
        "inviter": inv.inviter.username,
        "created_at": inv.created_at
    } for inv in invitations]

@router.post("/invitations/respond")
def respond_to_invitation(
    response: InvitationResponse,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Accept or decline a game invitation."""
    # Get game and check if it's still in setup
    game = db.query(Game).filter(Game.id == response.game_id).first()
    if not game or game.status != GameStatus.SETUP:
        raise HTTPException(404, "Game not found or no longer accepting players")
    
    # Get invitation
    invitation = db.query(GameInvitation).filter(
        and_(
            GameInvitation.game_id == response.game_id,
            GameInvitation.invitee_id == current_user.id,
            GameInvitation.status == InvitationStatus.PENDING
        )
    ).first()
    
    if not invitation:
        raise HTTPException(404, "Invitation not found")
    
    # Update invitation status
    invitation.status = InvitationStatus.ACCEPTED if response.response else InvitationStatus.DECLINED
    invitation.responded_at = datetime.now(timezone.utc)
    
    if response.response:
        # Add player to game
        player = Player(game_id=game.id, user_id=current_user.id)
        db.add(player)
    
    # Check if all invitations are responded to
    pending_count = db.query(GameInvitation).filter(
        and_(
            GameInvitation.game_id == game.id,
            GameInvitation.status == InvitationStatus.PENDING
        )
    ).count()
    
    accepted_count = db.query(Player).filter(Player.game_id == game.id).count()
    
    if pending_count == 0 and accepted_count >= 2:
        # All invitations responded and enough players accepted
        game.status = GameStatus.READY
    
    db.commit()
    
    return {"message": "Invitation response recorded"}

@router.post("/cleanup")
def cleanup_expired_games(db: Session = Depends(get_db)):
    """Cleanup games that have been in setup for more than 3 days."""
    expiry_date = datetime.now(timezone.utc) - timedelta(days=3)
    
    # Find expired games
    expired_games = db.query(Game).filter(
        and_(
            Game.status == GameStatus.SETUP,
            Game.created_at < expiry_date
        )
    ).all()
    
    for game in expired_games:
        # Update game status
        game.status = GameStatus.CANCELLED
        
        # Update pending invitations
        pending_invitations = db.query(GameInvitation).filter(
            and_(
                GameInvitation.game_id == game.id,
                GameInvitation.status == InvitationStatus.PENDING
            )
        ).all()
        
        for invitation in pending_invitations:
            invitation.status = InvitationStatus.EXPIRED
    
    db.commit()
    
    return {"expired_games_count": len(expired_games)} 