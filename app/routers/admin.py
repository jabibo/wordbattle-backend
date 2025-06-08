from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.dependencies import get_db
from app.auth import get_current_user, create_access_token
from app.models import User, WordList, Game, Player, Move, GameInvitation, ChatMessage
from app.wordlist import import_wordlist, load_wordlist_from_file
from passlib.context import CryptContext
from datetime import timedelta
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/debug/create-test-tokens")
async def create_test_tokens(
    db: Session = Depends(get_db)
):
    """
    DEBUG ENDPOINT: Create tokens for test users player01 and player02.
    This endpoint creates the users if they don't exist and returns their tokens.
    
    ⚠️ WARNING: This is for development/testing only!
    """
    # Disable in production
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=403, detail="Debug endpoints disabled in production")
    
    try:
        test_users = []
        
        # Define email mapping for test users
        email_mapping = {
            "player01": "player01@binge.de",
            "player02": "player02@binge.de"
        }
        
        for username in ["player01", "player02"]:
            # Check if user exists
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                # Create the user
                hashed_password = pwd_context.hash("testpassword123")
                user = User(
                    username=username,
                    email=email_mapping[username],
                    hashed_password=hashed_password,
                    is_email_verified=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"✅ Created test user: {username}")
            else:
                # Update email if it's different
                if user.email != email_mapping[username]:
                    user.email = email_mapping[username]
                    db.commit()
                    print(f"✅ Updated email for test user: {username}")
                else:
                    print(f"✅ Test user already exists: {username}")
            
            # Create token for the user
            access_token = create_access_token(
                data={"sub": str(user.id)},
                expires_delta=timedelta(days=30)  # Long-lived token for testing
            )
            
            test_users.append({
                "user_id": user.id,
                "username": username,
                "email": user.email,
                "access_token": access_token,
                "token_type": "bearer"
            })
        
        return {
            "message": "Test tokens created successfully",
            "users": test_users,
            "usage": {
                "description": "Use these tokens in the Authorization header",
                "format": "Bearer <access_token>",
                "example": f"Authorization: Bearer {test_users[0]['access_token'][:50]}..."
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating test tokens: {str(e)}")

@router.post("/wordlists/import")
async def import_wordlist_endpoint(
    language: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import a wordlist from a file into the database.
    
    Args:
        language: Language code (e.g., "de", "en")
        file: Uploaded wordlist file
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name
        content = await file.read()
        temp_file.write(content)
    
    try:
        # Check if words already exist for this language
        existing_count = db.query(WordList).filter(WordList.language == language).count()
        if existing_count > 0:
            # Delete existing words for this language
            db.query(WordList).filter(WordList.language == language).delete()
            db.commit()
        
        # Load words from file
        words = load_wordlist_from_file(temp_file_path)
        
        # Batch insert for better performance
        batch_size = 1000
        word_list = list(words)
        total_words = len(word_list)
        
        for i in range(0, total_words, batch_size):
            batch = [WordList(word=word, language=language) for word in word_list[i:i+batch_size]]
            db.add_all(batch)
            db.commit()
        
        return {
            "message": f"Successfully imported {total_words} words for language '{language}'",
            "language": language,
            "word_count": total_words
        }
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)

@router.get("/wordlists")
def list_wordlists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all available wordlists.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get language counts
    result = db.query(WordList.language, db.func.count(WordList.id)).group_by(WordList.language).all()
    
    return [
        {"language": language, "word_count": count}
        for language, count in result
    ]

@router.delete("/wordlists/{language}")
def delete_wordlist(
    language: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a wordlist for a specific language.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Delete words for this language
    count = db.query(WordList).filter(WordList.language == language).count()
    if count == 0:
        raise HTTPException(status_code=404, detail=f"No wordlist found for language '{language}'")
    
    db.query(WordList).filter(WordList.language == language).delete()
    db.commit()
    
    return {
        "message": f"Successfully deleted wordlist for language '{language}'",
        "language": language,
        "word_count": count
    }

def require_admin(current_user: User = Depends(get_current_user)):
    """Require the current user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, 
            detail="Admin privileges required"
        )
    return current_user

@router.post("/database/reset-games")
def reset_games_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Reset all game-related data while preserving users and wordlists.
    
    ⚠️ WARNING: This will delete:
    - All games and their state
    - All player records  
    - All moves history
    - All game invitations
    - All chat messages
    
    ✅ This will PRESERVE:
    - User accounts
    - WordLists
    """
    try:
        logger.info(f"Admin {current_user.username} initiated game data reset")
        
        # Get counts before deletion
        count_queries = [
            ("chat_messages", "Chat Messages"),
            ("moves", "Moves"),
            ("players", "Players"),
            ("game_invitations", "Game Invitations"),
            ("games", "Games")
        ]
        
        before_counts = {}
        for table, name in count_queries:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                before_counts[name] = result.scalar()
            except Exception as e:
                logger.warning(f"Could not count {table}: {e}")
                before_counts[name] = 0
        
        # Delete in order to respect foreign key constraints
        deleted_counts = {}
        
        # Delete chat messages
        result = db.query(ChatMessage).delete()
        deleted_counts["Chat Messages"] = result
        logger.info(f"Deleted {result} chat messages")
        
        # Delete moves
        result = db.query(Move).delete()
        deleted_counts["Moves"] = result
        logger.info(f"Deleted {result} moves")
        
        # Delete players
        result = db.query(Player).delete()
        deleted_counts["Players"] = result
        logger.info(f"Deleted {result} players")
        
        # Delete game invitations
        result = db.query(GameInvitation).delete()
        deleted_counts["Game Invitations"] = result
        logger.info(f"Deleted {result} game invitations")
        
        # Delete games
        result = db.query(Game).delete()
        deleted_counts["Games"] = result
        logger.info(f"Deleted {result} games")
        
        # Reset sequences
        sequences = [
            "chat_messages_id_seq",
            "moves_id_seq", 
            "players_id_seq",
            "game_invitations_id_seq"
        ]
        
        reset_sequences = []
        for seq in sequences:
            try:
                db.execute(text(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1"))
                reset_sequences.append(seq)
                logger.info(f"Reset sequence: {seq}")
            except Exception as e:
                logger.warning(f"Could not reset sequence {seq}: {e}")
        
        # Commit all changes
        db.commit()
        
        # Get final counts
        after_counts = {}
        for table, name in count_queries:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                after_counts[name] = result.scalar()
            except Exception as e:
                logger.warning(f"Could not count {table} after reset: {e}")
                after_counts[name] = 0
        
        logger.info(f"Game data reset completed successfully by admin {current_user.username}")
        
        return {
            "message": "Game data reset completed successfully",
            "admin": current_user.username,
            "before_counts": before_counts,
            "deleted_counts": deleted_counts,
            "after_counts": after_counts,
            "reset_sequences": reset_sequences,
            "preserved": ["Users", "WordLists"]
        }
        
    except Exception as e:
        logger.error(f"Error during game data reset by {current_user.username}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error during reset: {str(e)}")

@router.post("/database/reset-users-and-games")
def reset_all_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Reset ALL user and game data while preserving wordlists.
    
    ⚠️ DANGER: This will delete:
    - ALL user accounts (including the admin performing this action!)
    - All games and their state
    - All player records
    - All moves history
    - All game invitations 
    - All chat messages
    
    ✅ This will PRESERVE:
    - WordLists only
    
    Note: After this action, you will need to recreate admin accounts.
    """
    
    # Extra confirmation - require specific header for this dangerous operation
    try:
        logger.warning(f"DANGER: Admin {current_user.username} initiated FULL reset (users + games)")
        
        # Get counts before deletion
        count_queries = [
            ("chat_messages", "Chat Messages"),
            ("moves", "Moves"),
            ("players", "Players"),
            ("game_invitations", "Game Invitations"),
            ("games", "Games"),
            ("users", "Users")
        ]
        
        before_counts = {}
        for table, name in count_queries:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                before_counts[name] = result.scalar()
            except Exception as e:
                logger.warning(f"Could not count {table}: {e}")
                before_counts[name] = 0
        
        # Delete in order to respect foreign key constraints
        deleted_counts = {}
        
        # Delete chat messages
        result = db.query(ChatMessage).delete()
        deleted_counts["Chat Messages"] = result
        logger.info(f"Deleted {result} chat messages")
        
        # Delete moves
        result = db.query(Move).delete()
        deleted_counts["Moves"] = result
        logger.info(f"Deleted {result} moves")
        
        # Delete players
        result = db.query(Player).delete()
        deleted_counts["Players"] = result
        logger.info(f"Deleted {result} players")
        
        # Delete game invitations
        result = db.query(GameInvitation).delete()
        deleted_counts["Game Invitations"] = result
        logger.info(f"Deleted {result} game invitations")
        
        # Delete games
        result = db.query(Game).delete()
        deleted_counts["Games"] = result
        logger.info(f"Deleted {result} games")
        
        # Delete users (this will also delete the admin!)
        result = db.query(User).delete()
        deleted_counts["Users"] = result
        logger.info(f"Deleted {result} users")
        
        # Reset sequences
        sequences = [
            "chat_messages_id_seq",
            "moves_id_seq", 
            "players_id_seq",
            "game_invitations_id_seq",
            "users_id_seq"
        ]
        
        reset_sequences = []
        for seq in sequences:
            try:
                db.execute(text(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1"))
                reset_sequences.append(seq)
                logger.info(f"Reset sequence: {seq}")
            except Exception as e:
                logger.warning(f"Could not reset sequence {seq}: {e}")
        
        # Commit all changes
        db.commit()
        
        # Get final counts
        after_counts = {}
        for table, name in count_queries:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                after_counts[name] = result.scalar()
            except Exception as e:
                logger.warning(f"Could not count {table} after reset: {e}")
                after_counts[name] = 0
        
        logger.warning(f"FULL reset completed - all users deleted by former admin {current_user.username}")
        
        return {
            "message": "FULL reset completed - all users and games deleted",
            "warning": "All user accounts have been deleted, including admin accounts",
            "performed_by": current_user.username,
            "before_counts": before_counts,
            "deleted_counts": deleted_counts,
            "after_counts": after_counts,
            "reset_sequences": reset_sequences,
            "preserved": ["WordLists"],
            "next_steps": "You will need to recreate admin accounts using debug endpoints or database access"
        }
        
    except Exception as e:
        logger.error(f"Error during FULL reset by {current_user.username}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error during full reset: {str(e)}")