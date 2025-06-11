from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.auth import get_current_user, create_access_token
from app.models import User, WordList
from app.wordlist import import_wordlist, load_wordlist_from_file
from passlib.context import CryptContext
from datetime import timedelta
import os
import tempfile

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

@router.get("/dashboard")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get admin dashboard data including system stats and overview.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get user statistics
        total_users = db.query(User).count()
        admin_users = db.query(User).filter(User.is_admin == True).count()
        word_admin_users = db.query(User).filter(User.is_word_admin == True).count()
        
        # Get wordlist statistics
        wordlist_stats = db.query(WordList.language, db.func.count(WordList.id)).group_by(WordList.language).all()
        total_words = sum(count for _, count in wordlist_stats)
        
        # Get game statistics (if Game model exists)
        try:
            from app.models import Game
            total_games = db.query(Game).count()
        except ImportError:
            total_games = 0
        
        return {
            "system_stats": {
                "total_users": total_users,
                "admin_users": admin_users,
                "word_admin_users": word_admin_users,
                "total_games": total_games,
                "total_words": total_words
            },
            "wordlist_stats": [
                {"language": language, "word_count": count}
                for language, count in wordlist_stats
            ],
            "environment": os.getenv("ENVIRONMENT", "development"),
            "timestamp": "2025-06-11T12:43:55.629953Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")

@router.post("/database/import-wordlists")
async def bulk_import_wordlists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk import all available wordlists from the data directory.
    This endpoint imports all .txt files found in the data/ directory.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        data_dir = "data"
        if not os.path.exists(data_dir):
            raise HTTPException(status_code=404, detail="Data directory not found")
        
        imported_files = []
        errors = []
        
        # Find all .txt files in data directory
        for filename in os.listdir(data_dir):
            if filename.endswith('.txt'):
                file_path = os.path.join(data_dir, filename)
                
                # Extract language from filename (e.g., "de_words.txt" -> "de")
                language = filename.split('_')[0] if '_' in filename else filename.replace('.txt', '')
                
                try:
                    # Check if words already exist for this language
                    existing_count = db.query(WordList).filter(WordList.language == language).count()
                    if existing_count > 0:
                        # Delete existing words for this language
                        db.query(WordList).filter(WordList.language == language).delete()
                        db.commit()
                    
                    # Load words from file
                    words = load_wordlist_from_file(file_path)
                    
                    # Batch insert for better performance
                    batch_size = 1000
                    word_list = list(words)
                    total_words = len(word_list)
                    
                    for i in range(0, total_words, batch_size):
                        batch = [WordList(word=word, language=language) for word in word_list[i:i+batch_size]]
                        db.add_all(batch)
                        db.commit()
                    
                    imported_files.append({
                        "filename": filename,
                        "language": language,
                        "word_count": total_words
                    })
                    
                except Exception as e:
                    errors.append({
                        "filename": filename,
                        "error": str(e)
                    })
        
        if not imported_files and not errors:
            raise HTTPException(status_code=404, detail="No .txt files found in data directory")
        
        return {
            "message": f"Bulk import completed. {len(imported_files)} files imported successfully.",
            "imported_files": imported_files,
            "errors": errors,
            "total_imported": len(imported_files),
            "total_errors": len(errors)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during bulk import: {str(e)}")

@router.post("/database/reset-wordlists")
async def reset_wordlists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reset all wordlists in the database.
    This will delete all words and allow for fresh import.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get count before deletion
        word_count = db.query(WordList).count()
        
        # Delete all wordlists
        db.query(WordList).delete()
        db.commit()
        
        return {
            "message": f"Successfully reset wordlists. Deleted {word_count} words.",
            "deleted_count": word_count,
            "timestamp": "2025-06-11T12:43:55.629953Z"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting wordlists: {str(e)}")

@router.post("/database/reset-users")
async def reset_users(
    keep_admins: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reset user data (excluding admins by default).
    WARNING: This will delete user accounts and all associated data.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get counts before deletion
        total_users = db.query(User).count()
        
        if keep_admins:
            # Delete only non-admin users
            non_admin_users = db.query(User).filter(User.is_admin == False).all()
            deleted_count = len(non_admin_users)
            
            for user in non_admin_users:
                db.delete(user)
        else:
            # Delete all users (dangerous!)
            deleted_count = total_users
            db.query(User).delete()
        
        db.commit()
        
        remaining_users = db.query(User).count()
        
        return {
            "message": f"Successfully reset users. Deleted {deleted_count} users, {remaining_users} remaining.",
            "deleted_count": deleted_count,
            "remaining_count": remaining_users,
            "kept_admins": keep_admins,
            "timestamp": "2025-06-11T12:43:55.629953Z"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting users: {str(e)}")

@router.post("/database/reset-all")
async def reset_all_data(
    confirm: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    NUCLEAR OPTION: Reset ALL data in the database.
    WARNING: This will delete EVERYTHING except the current admin user.
    Requires explicit confirmation.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="This operation requires explicit confirmation. Set 'confirm=true' to proceed."
        )
    
    try:
        deletion_summary = {}
        
        # Get counts before deletion
        deletion_summary["wordlists_before"] = db.query(WordList).count()
        deletion_summary["users_before"] = db.query(User).count()
        
        # Import models to get Game, Player, etc.
        try:
            from app.models import Game, Player, GameInvitation
            deletion_summary["games_before"] = db.query(Game).count()
            deletion_summary["players_before"] = db.query(Player).count()
            deletion_summary["invitations_before"] = db.query(GameInvitation).count()
        except ImportError:
            deletion_summary["game_models"] = "Not available for deletion"
        
        # Delete wordlists
        db.query(WordList).delete()
        
        # Delete game data if available
        try:
            from app.models import Game, Player, GameInvitation, Move, ChatMessage
            db.query(ChatMessage).delete()
            db.query(Move).delete()
            db.query(Player).delete()
            db.query(GameInvitation).delete()
            db.query(Game).delete()
        except ImportError:
            pass
        
        # Delete non-admin users (keep current admin)
        non_admin_users = db.query(User).filter(
            User.is_admin == False
        ).all()
        
        for user in non_admin_users:
            db.delete(user)
        
        db.commit()
        
        # Get final counts
        deletion_summary["wordlists_after"] = db.query(WordList).count()
        deletion_summary["users_after"] = db.query(User).count()
        
        return {
            "message": "NUCLEAR RESET COMPLETED. All data deleted except admin users.",
            "warning": "This action cannot be undone.",
            "deletion_summary": deletion_summary,
            "remaining_admin": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email
            },
            "timestamp": "2025-06-11T12:43:55.629953Z"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error during nuclear reset: {str(e)}")