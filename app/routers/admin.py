from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
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
    result = db.query(WordList.language, func.count(WordList.id)).group_by(WordList.language).all()
    
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
        wordlist_stats = db.query(WordList.language, func.count(WordList.id)).group_by(WordList.language).all()
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

@router.get("/database/admin-status")
async def admin_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get admin user status information for the database"""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Count total users
        total_users = db.query(User).count()
        
        # Count admin users
        admin_users = db.query(User).filter(User.is_admin == True).all()
        admin_count = len(admin_users)
        
        # Count word admin users
        word_admin_count = db.query(User).filter(User.is_word_admin == True).count()
        
        # Get first few admin usernames for display (privacy-conscious)
        admin_usernames = [admin.username for admin in admin_users[:3]]
        
        return {
            "total_users": total_users,
            "admin_users": admin_count,
            "word_admin_users": word_admin_count,
            "has_admins": admin_count > 0,
            "admin_usernames": admin_usernames,
            "note": "First 3 admin usernames shown for privacy"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting admin status: {str(e)}")

@router.post("/database/reset-games")
async def reset_games(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ADMIN ONLY: Reset all game-related data while preserving users and wordlists.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        from sqlalchemy import text
        
        deleted_counts = {}
        
        # Get counts before deletion
        tables_to_reset = [
            ("chat_messages", "Chat Messages"),
            ("moves", "Moves"),
            ("players", "Players"),
            ("game_invitations", "Game Invitations"),
            ("games", "Games")
        ]
        
        # Delete in order to respect foreign key constraints
        for table, name in tables_to_reset:
            try:
                # Get count before deletion
                count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count_before = count_result.scalar()
                
                # Delete all records
                delete_result = db.execute(text(f"DELETE FROM {table}"))
                deleted_counts[table] = delete_result.rowcount
                
            except Exception as e:
                deleted_counts[table] = f"Error: {str(e)}"
        
        # Reset sequences
        sequences = [
            "chat_messages_id_seq",
            "moves_id_seq", 
            "players_id_seq",
            "game_invitations_id_seq",
            "games_id_seq"
        ]
        
        reset_sequences = []
        for seq in sequences:
            try:
                db.execute(text(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1"))
                reset_sequences.append(seq)
            except Exception as e:
                pass  # Sequence might not exist
        
        db.commit()
        
        return {
            "success": True,
            "message": "Game data reset completed successfully",
            "deleted_counts": deleted_counts,
            "reset_sequences": reset_sequences,
            "timestamp": "2025-06-11T12:43:55.629953Z"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting games: {str(e)}")

@router.post("/load-all-words")
async def load_all_words(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ADMIN ONLY: Load all remaining words into the database.
    This will complete the wordlist loading for German and English.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        from app.wordlist import load_wordlists_from_files
        
        # Check current word counts
        current_german = db.query(WordList).filter(WordList.language == "de").count()
        current_english = db.query(WordList).filter(WordList.language == "en").count()
        
        # Expected total counts
        expected_german = 601565
        expected_english = 178691
        
        if current_german >= expected_german and current_english >= expected_english:
            return {
                "success": True,
                "message": "All words already loaded",
                "current_counts": {
                    "german": current_german,
                    "english": current_english
                },
                "expected_counts": {
                    "german": expected_german,
                    "english": expected_english
                }
            }
        
        # Load all words from files (this will add missing words)
        loaded_counts = load_wordlists_from_files(db)
        
        # Get final counts
        final_german = db.query(WordList).filter(WordList.language == "de").count()
        final_english = db.query(WordList).filter(WordList.language == "en").count()
        
        return {
            "success": True,
            "message": "Word loading completed successfully",
            "before_counts": {
                "german": current_german,
                "english": current_english
            },
            "after_counts": {
                "german": final_german,
                "english": final_english
            },
            "loaded_this_session": loaded_counts,
            "total_words": final_german + final_english
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error loading words: {str(e)}")

@router.get("/performance")
async def get_performance_stats(
    current_user: User = Depends(get_current_user)
):
    """Get application performance statistics."""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        from app.middleware.performance import monitor
        from app.utils.cache import cache
        from datetime import datetime, timezone
        
        stats = monitor.get_stats()
        cache_stats = cache.stats()
        
        return {
            "performance": stats,
            "cache": cache_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance stats: {str(e)}")

@router.post("/database/create-default-admin")
async def create_default_admin(
    db: Session = Depends(get_db)
):
    """Create a default admin user for testing purposes"""
    try:
        from app.auth import get_password_hash
        from datetime import datetime, timezone
        
        # Check if an admin already exists
        existing_admin = db.query(User).filter(User.is_admin == True).first()
        if existing_admin:
            return {
                "message": "Admin user already exists",
                "admin_username": existing_admin.username,
                "action": "none"
            }
        
        # Create default admin user
        admin_username = "jan_admin"
        admin_password = "admin123"  # In production, use a secure password
        
        # Check if user with this username already exists
        existing_user = db.query(User).filter(User.username == admin_username).first()
        if existing_user:
            # Promote existing user to admin
            existing_user.is_admin = True
            db.commit()
            return {
                "message": f"Promoted existing user '{admin_username}' to admin",
                "admin_username": admin_username,
                "action": "promoted"
            }
        
        # Create new admin user
        admin_user = User(
            username=admin_username,
            email="jan@binge-dev.de",
            hashed_password=get_password_hash(admin_password),
            is_admin=True,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        return {
            "message": f"Created default admin user: {admin_username}",
            "admin_username": admin_username,
            "admin_id": admin_user.id,
            "password": admin_password,
            "action": "created",
            "note": "This is for testing only - change password in production!"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create admin user: {str(e)}")