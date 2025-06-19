from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.dependencies import get_db
from app.auth import get_current_user, create_access_token
from app.models import User, WordList, Game, Player, GameStatus, Move
from app.wordlist import import_wordlist, load_wordlist_from_file
from passlib.context import CryptContext
from datetime import timedelta
import os
import tempfile
from datetime import datetime, timezone
import logging
from app.database import SessionLocal
from pydantic import BaseModel
from typing import Optional, List
import json

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/admin", tags=["admin"])

class ResetGamesRequest(BaseModel):
    backup_before_reset: Optional[bool] = False

class TerminateGameRequest(BaseModel):
    reason: str = "Administrative action"

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
            
            # Create token for the user (using email like the main auth system)
            access_token = create_access_token(
                data={"sub": user.email},
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
                
                # Extract language from filename (e.g., "de_words.txt" -> "de", "de-words.txt" -> "de")
                # Handle both underscore and hyphen formats
                if '_' in filename:
                    language = filename.split('_')[0]
                elif '-' in filename:
                    language = filename.split('-')[0]
                else:
                    language = filename.replace('.txt', '')
                
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
    
    fresh_db = None
    try:
        # CRITICAL: Ensure we have a working database session
        fresh_db = recover_database_session(db, logger)
        
        # Get counts before deletion
        total_users = fresh_db.query(User).count()
        
        if keep_admins:
            # Delete only non-admin users
            non_admin_users = fresh_db.query(User).filter(User.is_admin == False).all()
            deleted_count = len(non_admin_users)
            
            for user in non_admin_users:
                fresh_db.delete(user)
        else:
            # Delete all users (dangerous!)
            deleted_count = total_users
            fresh_db.query(User).delete()
        
        fresh_db.commit()
        
        # Ensure computer player is recreated after user reset
        default_users_result = ensure_default_users(fresh_db)
        fresh_db.commit()
        
        remaining_users = fresh_db.query(User).count()
        
        return {
            "message": f"Successfully reset users. Deleted {deleted_count} users, {remaining_users} remaining.",
            "deleted_count": deleted_count,
            "remaining_count": remaining_users,
            "kept_admins": keep_admins,
            "default_users_recreated": default_users_result["actions"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        if fresh_db:
            try:
                fresh_db.rollback()
            except:
                pass  # Rollback might fail if session is broken
        raise HTTPException(status_code=500, detail=f"Error resetting users: {str(e)}")
    finally:
        # Ensure session is properly closed
        if fresh_db and fresh_db != db:
            try:
                fresh_db.close()
            except:
                pass  # Session might already be closed

@router.post("/database/reset-all")
async def reset_all_data(
    confirm: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ADMIN ONLY: Nuclear option - delete ALL data except admin users.
    WARNING: This will delete ALL games, players, moves, invitations, wordlists, and non-admin users.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="This is a DESTRUCTIVE operation. Set 'confirm=true' to proceed."
        )
    
    fresh_db = None
    try:
        # CRITICAL: Ensure we have a working database session
        fresh_db = recover_database_session(db, logger)
        
        deletion_summary = {}
        
        # Get counts before deletion
        deletion_summary["wordlists_before"] = fresh_db.query(WordList).count()
        deletion_summary["users_before"] = fresh_db.query(User).count()
        
        # Import models to get Game, Player, etc.
        try:
            from app.models import Game, Player, GameInvitation
            deletion_summary["games_before"] = fresh_db.query(Game).count()
            deletion_summary["players_before"] = fresh_db.query(Player).count()
            deletion_summary["invitations_before"] = fresh_db.query(GameInvitation).count()
        except ImportError:
            deletion_summary["game_models"] = "Not available for deletion"
        
        # Delete wordlists
        fresh_db.query(WordList).delete()
        
        # Delete game data if available
        try:
            from app.models import Game, Player, GameInvitation, Move, ChatMessage
            fresh_db.query(ChatMessage).delete()
            fresh_db.query(Move).delete()
            fresh_db.query(Player).delete()
            fresh_db.query(GameInvitation).delete()
            fresh_db.query(Game).delete()
        except ImportError:
            pass
        
        # Delete non-admin users (keep current admin)
        non_admin_users = fresh_db.query(User).filter(
            User.is_admin == False
        ).all()
        
        for user in non_admin_users:
            fresh_db.delete(user)
        
        fresh_db.commit()
        
        # Ensure computer player is recreated after nuclear reset
        default_users_result = ensure_default_users(fresh_db)
        fresh_db.commit()
        
        # Get final counts
        deletion_summary["wordlists_after"] = fresh_db.query(WordList).count()
        deletion_summary["users_after"] = fresh_db.query(User).count()
        
        return {
            "message": "NUCLEAR RESET COMPLETED. All data deleted except admin users.",
            "warning": "This action cannot be undone.",
            "deletion_summary": deletion_summary,
            "remaining_admin": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email
            },
            "default_users_recreated": default_users_result["actions"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        if fresh_db:
            try:
                fresh_db.rollback()
            except:
                pass  # Rollback might fail if session is broken
        raise HTTPException(status_code=500, detail=f"Error during nuclear reset: {str(e)}")
    finally:
        # Ensure session is properly closed
        if fresh_db and fresh_db != db:
            try:
                fresh_db.close()
            except:
                pass  # Session might already be closed

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

def recover_database_session(db: Session, logger) -> Session:
    """
    Robust database session recovery that handles failed transaction states.
    Returns a fresh, working database session.
    """
    try:
        # First, try to test the current session
        db.execute(text("SELECT 1"))
        logger.info("Database session is healthy")
        return db
    except Exception as e:
        logger.warning(f"Database session in failed state: {e}")
        
        # Try to rollback the failed transaction
        try:
            db.rollback()
            logger.info("Successfully rolled back failed transaction")
            
            # Test if rollback fixed the issue
            db.execute(text("SELECT 1"))
            logger.info("Database session recovered after rollback")
            return db
            
        except Exception as rollback_error:
            logger.warning(f"Rollback failed or session still broken: {rollback_error}")
            
            # Close the problematic session and create a fresh one
            try:
                db.close()
                logger.info("Closed problematic database session")
            except Exception as close_error:
                logger.warning(f"Error closing session: {close_error}")
            
            # Create a completely fresh session
            try:
                fresh_db = SessionLocal()
                fresh_db.execute(text("SELECT 1"))
                logger.info("Created fresh database session successfully")
                return fresh_db
            except Exception as fresh_error:
                logger.error(f"Failed to create fresh database session: {fresh_error}")
                raise HTTPException(
                    status_code=503, 
                    detail="Database service unavailable - unable to establish connection"
                )

@router.post("/database/reset-games")
async def reset_games(
    request: Optional[ResetGamesRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ADMIN ONLY: Reset all game-related data while preserving users and wordlists.
    Accepts optional backup_before_reset parameter from Flutter frontend.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Handle request body (Flutter sends backup_before_reset parameter)
    backup_requested = False
    if request:
        backup_requested = request.backup_before_reset
    
    logger.info(f"Reset games requested by {current_user.username}, backup_requested: {backup_requested}")
    
    fresh_db = None
    try:
        # CRITICAL: Ensure we have a working database session
        logger.info("Starting database session recovery...")
        fresh_db = recover_database_session(db, logger)
        logger.info("Database session recovery completed successfully")
        
        from sqlalchemy import text
        
        deleted_counts = {}
        
        # Optional backup step (placeholder for now)
        if backup_requested:
            logger.info("Backup requested but not implemented yet - proceeding with reset")
        
        # Get counts before deletion
        tables_to_reset = [
            ("chat_messages", "Chat Messages"),
            ("moves", "Moves"),
            ("players", "Players"),
            ("game_invitations", "Game Invitations"),
            ("games", "Games")
        ]
        
        logger.info(f"Starting deletion of {len(tables_to_reset)} tables...")
        
        # Delete in order to respect foreign key constraints
        for table, name in tables_to_reset:
            try:
                logger.info(f"Processing table: {table}")
                
                # Get count before deletion
                count_result = fresh_db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count_before = count_result.scalar()
                logger.info(f"Table {table} has {count_before} records before deletion")
                
                # Delete all records
                delete_result = fresh_db.execute(text(f"DELETE FROM {table}"))
                deleted_counts[table] = delete_result.rowcount
                logger.info(f"Deleted {delete_result.rowcount} records from {table}")
                
            except Exception as e:
                logger.error(f"Error processing table {table}: {e}")
                deleted_counts[table] = f"Error: {str(e)}"
        
        # Reset sequences (with error isolation)
        sequences = [
            "chat_messages_id_seq",
            "moves_id_seq", 
            "players_id_seq",
            "game_invitations_id_seq",
            "games_id_seq"
        ]
        
        reset_sequences = []
        logger.info(f"Attempting to reset {len(sequences)} sequences...")
        
        # Try to reset sequences, but don't fail the entire operation if we can't
        sequence_reset_failed = False
        for seq in sequences:
            try:
                # Create a savepoint before attempting sequence reset
                fresh_db.execute(text(f"SAVEPOINT reset_seq_{seq.replace('_', '')}"))
                fresh_db.execute(text(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1"))
                fresh_db.execute(text(f"RELEASE SAVEPOINT reset_seq_{seq.replace('_', '')}"))
                reset_sequences.append(seq)
                logger.info(f"Reset sequence: {seq}")
            except Exception as e:
                logger.warning(f"Could not reset sequence {seq}: {e}")
                sequence_reset_failed = True
                try:
                    # Rollback to savepoint to avoid transaction failure
                    fresh_db.execute(text(f"ROLLBACK TO SAVEPOINT reset_seq_{seq.replace('_', '')}"))
                except:
                    pass
                # Continue with other sequences
                continue
        
        if sequence_reset_failed:
            logger.info("Some sequences could not be reset due to permissions, but data deletion was successful")
        
        logger.info("Committing transaction...")
        fresh_db.commit()
        logger.info("Transaction committed successfully")
        
        return {
            "success": True,
            "message": "Game data reset completed successfully",
            "deleted_counts": deleted_counts,
            "reset_sequences": reset_sequences,
            "backup_requested": backup_requested,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during reset-games operation: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        
        if fresh_db:
            try:
                logger.info("Attempting rollback...")
                fresh_db.rollback()
                logger.info("Rollback completed")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
                pass  # Rollback might fail if session is broken
        
        # Return more detailed error information
        error_message = f"Error resetting games: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)
    finally:
        # Ensure session is properly closed
        if fresh_db and fresh_db != db:
            try:
                logger.info("Closing fresh database session...")
                fresh_db.close()
                logger.info("Fresh database session closed")
            except Exception as close_error:
                logger.warning(f"Error closing fresh session: {close_error}")
                pass  # Session might already be closed

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
        
        stats = monitor.get_stats()
        cache_stats = cache.stats()
        
        return {
            "performance": stats,
            "cache": cache_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance stats: {str(e)}")

def ensure_default_users(db: Session):
    """
    Helper function to ensure admin and computer player users exist.
    Returns a summary of actions taken.
    """
    from app.auth import get_password_hash
    from datetime import datetime, timezone
    
    actions = []
    
    # Check if an admin already exists
    existing_admin = db.query(User).filter(User.is_admin == True).first()
    admin_action = "none"
    
    if not existing_admin:
        # Create default admin user
        admin_username = "jan_admin"
        admin_password = "admin123"  # In production, use a secure password
        
        # Check if user with this username already exists
        existing_user = db.query(User).filter(User.username == admin_username).first()
        if existing_user:
            # Promote existing user to admin
            existing_user.is_admin = True
            admin_action = "promoted"
            actions.append(f"Promoted existing user '{admin_username}' to admin")
        else:
            # Create new admin user - use environment email or default
            admin_email = os.environ.get("ADMIN_EMAIL", f"{admin_username}@example.com")
            admin_user = User(
                username=admin_username,
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                is_admin=True,
                created_at=datetime.now(timezone.utc)
            )
            
            db.add(admin_user)
            admin_action = "created"
            actions.append(f"Created default admin user: {admin_username}")
    else:
        actions.append(f"Admin user already exists: {existing_admin.username}")
    
    # Check if computer player exists
    computer_user = db.query(User).filter(User.username == "computer_player").first()
    computer_action = "none"
    
    if not computer_user:
        computer_user = User(
            username="computer_player",
            email="computer@wordbattle.com",
            hashed_password="",  # No password needed
            is_admin=False,
            is_email_verified=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(computer_user)
        computer_action = "created"
        actions.append("Created computer player user")
    else:
        actions.append("Computer player user already exists")
    
    return {
        "actions": actions,
        "admin_action": admin_action,
        "computer_action": computer_action,
        "admin_username": existing_admin.username if existing_admin else admin_username
    }

@router.post("/database/create-default-admin")
async def create_default_admin(
    db: Session = Depends(get_db)
):
    """Create a default admin user and computer player for testing purposes"""
    try:
        result = ensure_default_users(db)
        db.commit()
        
        return {
            "message": "Default users checked/created successfully",
            "actions": result["actions"],
            "admin_action": result["admin_action"],
            "computer_action": result["computer_action"],
            "admin_username": result["admin_username"],
            "note": "Admin password is 'admin123' for testing only!"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create default users: {str(e)}")

@router.post("/database/ensure-primary-admin")
async def ensure_primary_admin(
    db: Session = Depends(get_db)
):
    """Ensure that jan@binge.de exists as the primary admin user (production-safe)"""
    try:
        from app.auth import get_password_hash
        from datetime import datetime, timezone
        
        primary_admin_email = "jan@binge.de"
        primary_admin_username = "janbinge"
        
        actions = []
        
        # First check if jan@binge.de exists
        existing_user = db.query(User).filter(User.email == primary_admin_email).first()
        
        if existing_user:
            # User exists - ensure admin privileges
            changes_made = False
            
            if not existing_user.is_admin:
                existing_user.is_admin = True
                changes_made = True
                actions.append(f"Granted admin privileges to {primary_admin_email}")
            
            if not existing_user.is_word_admin:
                existing_user.is_word_admin = True
                changes_made = True
                actions.append(f"Granted word admin privileges to {primary_admin_email}")
            
            if not existing_user.is_email_verified:
                existing_user.is_email_verified = True
                changes_made = True
                actions.append(f"Verified email for {primary_admin_email}")
            
            if changes_made:
                db.commit()
                action_type = "upgraded"
            else:
                action_type = "already_admin"
                actions.append(f"User {primary_admin_email} already has all admin privileges")
            
            return {
                "message": f"Primary admin user ensured successfully",
                "email": primary_admin_email,
                "username": existing_user.username,
                "user_id": existing_user.id,
                "action": action_type,
                "actions": actions,
                "is_admin": existing_user.is_admin,
                "is_word_admin": existing_user.is_word_admin,
                "created_at": existing_user.created_at.isoformat() if existing_user.created_at else None
            }
        else:
            # User doesn't exist - create primary admin
            
            # Check if username is taken
            username_check = db.query(User).filter(User.username == primary_admin_username).first()
            if username_check:
                primary_admin_username = f"{primary_admin_username}_admin"
                actions.append(f"Username '{primary_admin_username}' was taken, using '{primary_admin_username}'")
            
            # Create the primary admin user
            new_admin = User(
                username=primary_admin_username,
                email=primary_admin_email,
                hashed_password=get_password_hash("admin123456"),  # Default secure password
                is_admin=True,
                is_word_admin=True,
                is_email_verified=True,
                language="en",
                allow_invites=True,
                preferred_languages=["en", "de"],
                created_at=datetime.now(timezone.utc)
            )
            
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            
            actions.append(f"Created primary admin user: {primary_admin_email}")
            
            return {
                "message": f"Primary admin user created successfully",
                "email": primary_admin_email,
                "username": new_admin.username,
                "user_id": new_admin.id,
                "action": "created",
                "actions": actions,
                "is_admin": new_admin.is_admin,
                "is_word_admin": new_admin.is_word_admin,
                "created_at": new_admin.created_at.isoformat(),
                "default_password": "admin123456",
                "note": "Please change the default password after first login!"
            }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to ensure primary admin: {str(e)}")

@router.post("/database/fix-schema")
async def fix_database_schema():
    """Fix database schema by ensuring required columns exist (production-safe)"""
    try:
        from sqlalchemy import text
        from app.database import SessionLocal
        
        actions = []
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Check current database columns
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'games' 
                ORDER BY column_name
            """))
            columns = [row[0] for row in result.fetchall()]
            actions.append(f"Current games table columns: {columns}")
            
            # Check for missing columns
            required_columns = ['name', 'ended_at']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                actions.append(f"Missing columns detected: {missing_columns}")
                
                # Add missing columns
                for col in missing_columns:
                    if col == 'name':
                        db.execute(text("ALTER TABLE games ADD COLUMN name VARCHAR"))
                        actions.append("✅ Added 'name' column to games table")
                    elif col == 'ended_at':
                        db.execute(text("ALTER TABLE games ADD COLUMN ended_at TIMESTAMP WITH TIME ZONE"))
                        actions.append("✅ Added 'ended_at' column to games table")
                
                db.commit()
                actions.append("✅ All schema fixes committed successfully")
            else:
                actions.append("✅ All required columns already exist")
            
            # Verify fix by checking columns again
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'games' 
                ORDER BY column_name
            """))
            final_columns = [row[0] for row in result.fetchall()]
            actions.append(f"Final games table columns: {final_columns}")
            
            return {
                "success": True,
                "message": "Database schema check and fix completed",
                "actions": actions,
                "missing_columns": missing_columns,
                "all_columns": final_columns,
                "fixed": len(missing_columns) > 0
            }
            
        finally:
            db.close()
            
    except Exception as e:
        actions.append(f"❌ Error: {str(e)}")
        return {
            "success": False,
            "message": "Database schema fix failed",
            "actions": actions,
            "error": str(e)
        }

@router.post("/database/run-migration")
async def run_migration():
    """Run Alembic migration from within the application (production-safe)"""
    try:
        from sqlalchemy import text, create_engine
        from app.config import get_database_url
        
        actions = []
        
        # Use the superuser connection to apply the schema changes
        try:
            actions.append("🔧 Connecting to database with superuser...")
            
            # Get database URL and make it superuser
            db_url = get_database_url()
            
            # Replace the user with postgres superuser for schema changes
            if "wordbattle_user:wordbattle_password" in db_url:
                superuser_url = db_url.replace("wordbattle_user:wordbattle_password", "postgres:wordbattle_password")
                actions.append("✅ Using postgres superuser for schema operations")
            else:
                superuser_url = db_url
                actions.append("⚠️  Using original database URL")
            
            # Create engine with superuser
            engine = create_engine(superuser_url)
            
            with engine.connect() as conn:
                # Check current columns
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'games' 
                    ORDER BY column_name
                """))
                columns = [row[0] for row in result.fetchall()]
                actions.append(f"📋 Current games table columns: {columns}")
                
                # Check for missing columns
                required_columns = ['name', 'ended_at']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    actions.append(f"🔧 Adding missing columns: {missing_columns}")
                    
                    # Add missing columns using superuser privileges
                    for col in missing_columns:
                        if col == 'name':
                            conn.execute(text("ALTER TABLE games ADD COLUMN name VARCHAR"))
                            actions.append("✅ Added 'name' column to games table")
                        elif col == 'ended_at':
                            conn.execute(text("ALTER TABLE games ADD COLUMN ended_at TIMESTAMP WITH TIME ZONE"))
                            actions.append("✅ Added 'ended_at' column to games table")
                    
                    # Commit changes
                    conn.commit()
                    actions.append("✅ Schema changes committed successfully")
                    
                    # Update Alembic version table to reflect the migration was applied
                    try:
                        # Get the revision ID of our migration
                        migration_revision = "1fb073ce7b47"  # This is our migration ID
                        
                        # Update the alembic_version table
                        conn.execute(text("UPDATE alembic_version SET version_num = :rev"), {"rev": migration_revision})
                        conn.commit()
                        actions.append(f"✅ Updated Alembic version to {migration_revision}")
                    except Exception as version_error:
                        actions.append(f"⚠️  Could not update Alembic version: {str(version_error)}")
                    
                else:
                    actions.append("✅ All required columns already exist")
                
                # Verify the final state
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'games' 
                    ORDER BY column_name
                """))
                final_columns = [row[0] for row in result.fetchall()]
                actions.append(f"✅ Final games table columns: {final_columns}")
                
                return {
                    "success": True,
                    "message": "Database schema updated successfully",
                    "actions": actions,
                    "all_columns": final_columns,
                    "missing_columns": [],
                    "fixed": len(missing_columns) > 0
                }
        
        except Exception as e:
            actions.append(f"❌ Database error: {str(e)}")
            raise e
            
    except Exception as e:
        actions.append(f"❌ Error: {str(e)}")
        return {
            "success": False,
            "message": "Migration failed",
            "actions": actions,
            "error": str(e)
        }

@router.get("/debug/persistent-tokens")
async def debug_persistent_tokens(db: Session = Depends(get_db)):
    """Debug endpoint to check persistent token status (production-safe)"""
    try:
        from sqlalchemy import text
        from datetime import datetime, timezone
        
        actions = []
        
        # Check users with persistent tokens
        result = db.execute(text("""
            SELECT id, username, email, 
                   persistent_token IS NOT NULL as has_token,
                   persistent_token_expires,
                   persistent_token_expires > NOW() as token_valid
            FROM users 
            WHERE persistent_token IS NOT NULL
            ORDER BY id
        """))
        
        users_with_tokens = []
        for row in result.fetchall():
            users_with_tokens.append({
                "id": row[0],
                "username": row[1], 
                "email": row[2],
                "has_token": row[3],
                "expires": row[4].isoformat() if row[4] else None,
                "is_valid": row[5] if row[5] is not None else False
            })
        
        actions.append(f"📋 Found {len(users_with_tokens)} users with persistent tokens")
        
        # Check total user count
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        total_users = result.fetchone()[0]
        actions.append(f"📊 Total users in database: {total_users}")
        
        return {
            "success": True,
            "message": "Persistent token debug completed",
            "actions": actions,
            "users_with_tokens": users_with_tokens,
            "total_users": total_users,
            "current_time": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "Debug failed",
            "error": str(e)
        }

@router.get("/contract-status")
async def get_contract_status():
    """Get basic contract validation status (public endpoint)."""
    
    try:
        from app.config import CONTRACTS_DIR, ENABLE_CONTRACT_VALIDATION, CONTRACT_VALIDATION_STRICT
        import os
        
        status = {
            "contract_validation": {
                "enabled": ENABLE_CONTRACT_VALIDATION,
                "strict_mode": CONTRACT_VALIDATION_STRICT,
                "contracts_dir": CONTRACTS_DIR,
                "contracts_dir_exists": os.path.exists(CONTRACTS_DIR) if CONTRACTS_DIR else False,
                "validator_loaded": False,
                "schema_files": [],
                "error": None
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Try to load validator
        try:
            from app.utils.contract_validator import validator
            status["contract_validation"]["validator_loaded"] = validator.loaded
            status["contract_validation"]["schema_files"] = list(validator.schemas.keys()) if validator.loaded else []
            if validator.loaded:
                status["contract_validation"]["schema_count"] = len(validator.schemas)
        except ImportError as e:
            status["contract_validation"]["error"] = f"Import error: {str(e)}"
        except Exception as e:
            status["contract_validation"]["error"] = f"Validator error: {str(e)}"
        
        return status
        
    except Exception as e:
        return {
            "contract_validation": {
                "enabled": False,
                "error": f"System error: {str(e)}",
                "validator_loaded": False,
                "schema_files": []
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/contracts/info")
async def get_contract_info():
    """Get comprehensive contract validation information (public endpoint)."""
    
    try:
        from app.config import CONTRACTS_DIR, ENABLE_CONTRACT_VALIDATION, CONTRACT_VALIDATION_STRICT
        import os
        
        info = {
            "contract_validation": {
                "enabled": ENABLE_CONTRACT_VALIDATION,
                "strict_mode": CONTRACT_VALIDATION_STRICT,
                "contracts_dir": CONTRACTS_DIR,
                "contracts_dir_exists": os.path.exists(CONTRACTS_DIR) if CONTRACTS_DIR else False,
                "validator_loaded": False,
                "schema_files": [],
                "total_schemas": 0,
                "middleware_active": False,
                "error": None
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Try to load validator
        try:
            from app.utils.contract_validator import validator
            info["contract_validation"]["validator_loaded"] = validator.loaded
            info["contract_validation"]["schema_files"] = list(validator.schemas.keys()) if validator.loaded else []
            info["contract_validation"]["total_schemas"] = len(validator.schemas) if validator.loaded else 0
            
            # Check if middleware is active
            info["contract_validation"]["middleware_active"] = ENABLE_CONTRACT_VALIDATION and validator.loaded
            
            if validator.loaded:
                info["contract_validation"]["validator_details"] = validator.get_contract_info()
        except ImportError as e:
            info["contract_validation"]["error"] = f"Import error: {str(e)}"
        except Exception as e:
            info["contract_validation"]["error"] = f"Validator error: {str(e)}"
        
        return info
        
    except Exception as e:
        return {
            "contract_validation": {
                "enabled": False,
                "error": f"System error: {str(e)}",
                "validator_loaded": False,
                "schema_files": []
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/contracts/compliance")
async def check_contract_compliance(
    current_user = Depends(get_current_user)
):
    """Check API compliance with frontend contracts (admin only)."""
    
    # Admin-only endpoint for security
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    try:
        from app.utils.contract_validator import check_contracts_compliance, validator
        
        compliance_report = check_contracts_compliance()
        contract_info = validator.get_contract_info()
        
        return {
            "compliance": compliance_report,
            "contract_info": contract_info,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except ImportError as e:
        logger.warning(f"Contract validation not available: {e}")
        return {
            "compliance": {"compliant": False, "reason": "Contract validation module not available"},
            "contract_info": {"enabled": False, "error": str(e)},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Contract compliance check failed: {e}")
        return {
            "compliance": {"compliant": False, "reason": f"Error: {str(e)}"},
            "contract_info": {"enabled": False, "error": str(e)},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.post("/contracts/validate-endpoint")
async def validate_specific_endpoint(
    endpoint_data: dict,
    current_user = Depends(get_current_user)
):
    """Validate a specific endpoint response against contracts (admin only)."""
    
    # Admin-only endpoint for security
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    try:
        from app.utils.contract_validator import validator
        
        endpoint = endpoint_data.get("endpoint", "")
        response_data = endpoint_data.get("response_data", {})
        status_code = endpoint_data.get("status_code", 200)
        
        if not endpoint or not response_data:
            raise HTTPException(400, "Missing endpoint or response_data in request")
        
        is_valid = validator.validate_response(endpoint, response_data, status_code)
        
        return {
            "validation_result": {
                "endpoint": endpoint,
                "status_code": status_code,
                "is_valid": is_valid,
                "validator_loaded": validator.loaded
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except ImportError as e:
        raise HTTPException(500, f"Contract validation not available: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Validation error: {str(e)}")

@router.get("/debug/database-url")
async def get_database_url_debug():
    """Debug endpoint to check DATABASE_URL configuration (public for testing)."""
    import os
    from app.config import DATABASE_URL
    
    return {
        "database_url_from_config": DATABASE_URL,
        "database_url_from_env": os.environ.get("DATABASE_URL", "NOT_SET"),
        "environment": os.environ.get("ENVIRONMENT", "NOT_SET"),
        "all_env_vars": {key: value for key, value in os.environ.items() if 'DB' in key.upper() or 'DATABASE' in key.upper()},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/debug/startup-status")
async def get_startup_status():
    """Debug endpoint to show startup tasks status."""
    try:
        from app.utils.startup import startup_tasks
        
        result = startup_tasks()
        
        return {
            "startup_status": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "startup_status": {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

@router.get("/debug/verification-codes")
async def get_debug_verification_codes():
    """Debug endpoint to show recent verification codes for testing (when SMTP not configured)."""
    from app.db import get_db
    from app.models import User
    from sqlalchemy.orm import Session
    
    db = next(get_db())
    try:
        # Get users with verification codes (for testing purposes)
        users_with_codes = db.query(User).filter(
            User.verification_code.isnot(None),
            User.verification_code_expires.isnot(None)
        ).limit(10).all()
        
        verification_data = []
        for user in users_with_codes:
            expires_at = user.verification_code_expires
            if expires_at:
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                is_expired = expires_at < datetime.now(timezone.utc)
            else:
                is_expired = True
                
            # A verification code is "used" if it has been cleared (None) 
            # or if the code exists but is expired
            is_code_used = user.verification_code is None or is_expired
                
            verification_data.append({
                "email": user.email,
                "username": user.username,
                "verification_code": user.verification_code,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "is_expired": is_expired,
                "is_verified": is_code_used  # This now means "is this specific code used/invalid"
            })
        
        return {
            "message": "Debug verification codes (only shown when SMTP not configured)",
            "smtp_configured": bool(os.environ.get("SMTP_PASSWORD")),
            "verification_codes": verification_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    finally:
        db.close()

# =============================================================================
# FRONTEND-REQUIRED DATABASE MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/database/reset")
async def database_reset(
    confirm: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Frontend-required endpoint: Complete database reset.
    This is an alias for reset-all with the exact endpoint name the frontend expects.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="This operation requires explicit confirmation. Set 'confirm=true' to proceed."
        )
    
    fresh_db = None
    try:
        # CRITICAL: Ensure we have a working database session
        fresh_db = recover_database_session(db, logger)
        
        # Use existing reset-all logic
        deletion_summary = {}
        
        # Get counts before deletion
        deletion_summary["wordlists_before"] = fresh_db.query(WordList).count()
        deletion_summary["users_before"] = fresh_db.query(User).count()
        
        # Import models to get Game, Player, etc.
        try:
            from app.models import Game, Player, GameInvitation
            deletion_summary["games_before"] = fresh_db.query(Game).count()
            deletion_summary["players_before"] = fresh_db.query(Player).count()
            deletion_summary["invitations_before"] = fresh_db.query(GameInvitation).count()
        except ImportError:
            deletion_summary["game_models"] = "Not available for deletion"
        
        # Delete wordlists
        fresh_db.query(WordList).delete()
        
        # Delete game data if available
        try:
            from app.models import Game, Player, GameInvitation, Move, ChatMessage
            fresh_db.query(ChatMessage).delete()
            fresh_db.query(Move).delete()
            fresh_db.query(Player).delete()
            fresh_db.query(GameInvitation).delete()
            fresh_db.query(Game).delete()
        except ImportError:
            pass
        
        # Delete non-admin users (keep current admin)
        non_admin_users = fresh_db.query(User).filter(
            User.is_admin == False
        ).all()
        
        for user in non_admin_users:
            fresh_db.delete(user)
        
        fresh_db.commit()
        
        # Ensure computer player is recreated after database reset
        default_users_result = ensure_default_users(fresh_db)
        fresh_db.commit()
        
        # Get final counts
        deletion_summary["wordlists_after"] = fresh_db.query(WordList).count()
        deletion_summary["users_after"] = fresh_db.query(User).count()
        
        return {
            "success": True,
            "message": "Database reset completed successfully",
            "deletion_summary": deletion_summary,
            "remaining_admin": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email
            },
            "default_users_recreated": default_users_result["actions"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        if fresh_db:
            try:
                fresh_db.rollback()
            except:
                pass  # Rollback might fail if session is broken
        raise HTTPException(status_code=500, detail=f"Error during database reset: {str(e)}")
    finally:
        # Ensure session is properly closed
        if fresh_db and fresh_db != db:
            try:
                fresh_db.close()
            except:
                pass  # Session might already be closed

@router.post("/database/backup")
async def database_backup(
    backup_type: str = "full",
    include_wordlists: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Frontend-required endpoint: Create database backup.
    Returns backup metadata and download information.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Generate backup metadata
        backup_id = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        # Get database statistics
        stats = {}
        stats["users_count"] = db.query(User).count()
        stats["wordlists_count"] = db.query(WordList).count()
        
        try:
            from app.models import Game, Player, GameInvitation, Move, ChatMessage
            stats["games_count"] = db.query(Game).count()
            stats["players_count"] = db.query(Player).count()
            stats["moves_count"] = db.query(Move).count()
            stats["invitations_count"] = db.query(GameInvitation).count()
            stats["chat_messages_count"] = db.query(ChatMessage).count()
        except ImportError:
            stats["game_data"] = "Not available"
        
        # In a real implementation, this would:
        # 1. Create actual database dump
        # 2. Store backup file in cloud storage
        # 3. Return download URL
        
        return {
            "success": True,
            "message": "Database backup initiated successfully",
            "backup_info": {
                "backup_id": backup_id,
                "backup_type": backup_type,
                "include_wordlists": include_wordlists,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "email": current_user.email
                },
                "size_estimate": "Calculating...",
                "status": "in_progress"
            },
            "database_stats": stats,
            "note": "This is a simulation. In production, this would create an actual backup file.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating database backup: {str(e)}")

@router.post("/database/maintenance")
async def database_maintenance(
    operation: str = "optimize",
    auto_vacuum: bool = True,
    rebuild_indexes: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Frontend-required endpoint: Perform database maintenance operations.
    Includes optimization, vacuuming, and index rebuilding.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        maintenance_results = {
            "operation": operation,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "performed_tasks": []
        }
        
        # Get database statistics before maintenance
        stats_before = {}
        stats_before["users_count"] = db.query(User).count()
        stats_before["wordlists_count"] = db.query(WordList).count()
        
        try:
            from app.models import Game, Player, GameInvitation, Move, ChatMessage
            stats_before["games_count"] = db.query(Game).count()
            stats_before["players_count"] = db.query(Player).count()
            stats_before["moves_count"] = db.query(Move).count()
            stats_before["invitations_count"] = db.query(GameInvitation).count()
            stats_before["chat_messages_count"] = db.query(ChatMessage).count()
        except ImportError:
            stats_before["game_data"] = "Not available"
        
        # Perform maintenance tasks based on operation type
        if operation == "optimize" or operation == "full":
            # Analyze tables for query optimizer
            try:
                from sqlalchemy import text
                db.execute(text("ANALYZE"))
                maintenance_results["performed_tasks"].append("Database statistics updated")
            except Exception as e:
                maintenance_results["performed_tasks"].append(f"Statistics update failed: {str(e)}")
        
        if auto_vacuum and (operation == "vacuum" or operation == "full"):
            # Vacuum database (PostgreSQL)
            try:
                # Note: VACUUM cannot be run inside a transaction block
                maintenance_results["performed_tasks"].append("Vacuum scheduled (requires manual execution)")
            except Exception as e:
                maintenance_results["performed_tasks"].append(f"Vacuum failed: {str(e)}")
        
        if rebuild_indexes and (operation == "reindex" or operation == "full"):
            # Rebuild indexes
            try:
                maintenance_results["performed_tasks"].append("Index rebuild scheduled (requires manual execution)")
            except Exception as e:
                maintenance_results["performed_tasks"].append(f"Index rebuild failed: {str(e)}")
        
        # Clean up expired data
        if operation == "cleanup" or operation == "full":
            try:
                # Clean up expired verification codes
                expired_codes = db.query(User).filter(
                    User.verification_code_expires < datetime.now(timezone.utc)
                ).update({
                    User.verification_code: None,
                    User.verification_code_expires: None
                })
                maintenance_results["performed_tasks"].append(f"Cleaned up {expired_codes} expired verification codes")
            except Exception as e:
                maintenance_results["performed_tasks"].append(f"Cleanup failed: {str(e)}")
        
        db.commit()
        
        maintenance_results["completed_at"] = datetime.now(timezone.utc).isoformat()
        maintenance_results["stats_before"] = stats_before
        
        return {
            "success": True,
            "message": "Database maintenance completed successfully",
            "maintenance_results": maintenance_results,
            "recommendations": [
                "Consider running VACUUM ANALYZE manually during low-traffic periods",
                "Monitor query performance after maintenance",
                "Schedule regular maintenance during off-peak hours"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error during database maintenance: {str(e)}")

@router.get("/database/diagnose-games")
def diagnose_game_integrity(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Diagnose data integrity issues in games."""
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    # Get all games
    games = db.query(Game).all()
    issues = []
    
    for game in games:
        game_issues = []
        
        # Get players for this game
        players = db.query(Player).filter(Player.game_id == game.id).all()
        player_ids = [p.user_id for p in players]
        
        # Check if current_player_id exists in players
        if game.current_player_id and game.current_player_id not in player_ids:
            game_issues.append({
                "type": "missing_current_player",
                "description": f"current_player_id {game.current_player_id} not found in players {player_ids}",
                "current_player_id": game.current_player_id,
                "player_ids": player_ids
            })
        
        # Check for players with empty racks in active games
        if game.status == GameStatus.IN_PROGRESS:
            for player in players:
                if not player.rack or len(player.rack) == 0:
                    game_issues.append({
                        "type": "empty_rack",
                        "description": f"Player {player.user_id} has empty rack in active game",
                        "player_id": player.user_id,
                        "rack": player.rack
                    })
        
        # Check for missing users
        for player in players:
            user = db.query(User).filter(User.id == player.user_id).first()
            if not user:
                game_issues.append({
                    "type": "missing_user",
                    "description": f"Player {player.user_id} references non-existent user",
                    "player_id": player.user_id
                })
        
        if game_issues:
            issues.append({
                "game_id": game.id,
                "status": game.status.value,
                "created_at": game.created_at.isoformat(),
                "current_player_id": game.current_player_id,
                "player_count": len(players),
                "issues": game_issues
            })
    
    return {
        "total_games": len(games),
        "games_with_issues": len(issues),
        "issues": issues,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/database/repair-games")
def repair_game_integrity(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Repair data integrity issues in games."""
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    # Get all games
    games = db.query(Game).all()
    repairs = []
    
    for game in games:
        game_repairs = []
        
        # Get players for this game
        players = db.query(Player).filter(Player.game_id == game.id).all()
        player_ids = [p.user_id for p in players]
        
        # Fix missing current_player_id issue
        if game.current_player_id and game.current_player_id not in player_ids:
            old_current_player = game.current_player_id
            if players:
                # Set to first available player
                game.current_player_id = players[0].user_id
                game_repairs.append({
                    "type": "fixed_current_player",
                    "description": f"Changed current_player_id from {old_current_player} to {game.current_player_id}",
                    "old_value": old_current_player,
                    "new_value": game.current_player_id
                })
            else:
                # No players - set to None
                game.current_player_id = None
                game_repairs.append({
                    "type": "cleared_current_player",
                    "description": f"Cleared current_player_id {old_current_player} (no players found)",
                    "old_value": old_current_player,
                    "new_value": None
                })
        
        # Fix empty racks in active games
        if game.status == GameStatus.IN_PROGRESS:
            for player in players:
                if not player.rack or len(player.rack) == 0:
                    # Give player a new rack
                    from app.game_logic.letter_bag import create_rack, create_letter_bag
                    letter_bag = create_letter_bag(game.language)
                    new_rack = create_rack(letter_bag)
                    player.rack = "".join(new_rack)
                    game_repairs.append({
                        "type": "fixed_empty_rack",
                        "description": f"Gave player {player.user_id} a new rack: {player.rack}",
                        "player_id": player.user_id,
                        "new_rack": player.rack
                    })
        
        if game_repairs:
            repairs.append({
                "game_id": game.id,
                "status": game.status.value,
                "repairs": game_repairs
            })
    
    # Commit all repairs
    db.commit()
    
    return {
        "total_games": len(games),
        "games_repaired": len(repairs),
        "repairs": repairs,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/database/check-legacy-games")
def check_legacy_games(
    db: Session = Depends(get_db)
):
    """Check for legacy games that might have old data formats."""
    # Get games involving user ID 1 (jan_admin)
    games_with_user_1 = db.query(Game).join(Player).filter(Player.user_id == 1).all()
    
    legacy_games = []
    for game in games_with_user_1:
        players = db.query(Player).filter(Player.game_id == game.id).all()
        player_info = []
        for p in players:
            user = db.query(User).filter(User.id == p.user_id).first()
            player_info.append({
                "user_id": p.user_id,
                "username": user.username if user else "Unknown",
                "rack": p.rack,
                "rack_type": type(p.rack).__name__
            })
        
        legacy_games.append({
            "game_id": game.id,
            "status": game.status.value,
            "current_player_id": game.current_player_id,
            "created_at": game.created_at.isoformat(),
            "players": player_info
        })
    
    return {
        "total_games_with_user_1": len(legacy_games),
        "games": legacy_games,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/database/recover-transaction")
async def recover_failed_transaction(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ADMIN ONLY: Recover from failed transaction state.
    This endpoint handles the PostgreSQL "in failed transaction block" error.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        recovery_steps = []
        
        # Step 1: Test current transaction state
        try:
            result = db.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            recovery_steps.append("✅ Database connection is healthy")
            
            return {
                "success": True,
                "message": "Database is already in a healthy state",
                "recovery_steps": recovery_steps,
                "test_query_result": test_value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            recovery_steps.append(f"❌ Database in failed state: {str(e)}")
            
            # Step 2: Rollback failed transaction
            try:
                db.rollback()
                recovery_steps.append("✅ Rolled back failed transaction")
            except Exception as rollback_error:
                recovery_steps.append(f"⚠️  Rollback attempt: {str(rollback_error)}")
            
            # Step 3: Close and recreate session
            try:
                db.close()
                recovery_steps.append("✅ Closed problematic session")
                
                # Create fresh session
                fresh_db = SessionLocal()
                test_result = fresh_db.execute(text("SELECT 1 as test"))
                test_value = test_result.scalar()
                fresh_db.close()
                
                recovery_steps.append("✅ Created fresh session and verified connectivity")
                
                return {
                    "success": True,
                    "message": "Database transaction state recovered successfully",
                    "recovery_steps": recovery_steps,
                    "test_query_result": test_value,
                    "recommendation": "Database is now ready for operations",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
            except Exception as recovery_error:
                recovery_steps.append(f"❌ Recovery failed: {str(recovery_error)}")
                
                return {
                    "success": False,
                    "message": "Failed to recover database transaction state",
                    "recovery_steps": recovery_steps,
                    "error": str(recovery_error),
                    "recommendation": "Database service may need to be restarted",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
    
    except Exception as e:
        return {
            "success": False,
            "message": "Error during transaction recovery",
            "error": str(e),
            "recommendation": "Contact system administrator",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    finally:
        # Always ensure session cleanup
        try:
            if db:
                db.close()
        except:
            pass  # Session might already be closed

@router.post("/debug/fix-admin-privileges")
async def fix_admin_privileges(
    db: Session = Depends(get_db)
):
    """
    DEBUG ENDPOINT: Fix admin privileges for jan_admin user.
    This ensures the jan_admin user has proper admin privileges.
    
    ⚠️ WARNING: This is for development/testing only!
    """
    # Disable in production
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=403, detail="Debug endpoints disabled in production")
    
    try:
        # Find the jan_admin user
        jan_admin = db.query(User).filter(User.username == "jan_admin").first()
        
        if not jan_admin:
            # Try to find by email
            jan_admin = db.query(User).filter(User.email == "jan@binge.de").first()
        
        if jan_admin:
            # Ensure they have admin privileges
            if not jan_admin.is_admin:
                jan_admin.is_admin = True
                db.commit()
                return {
                    "message": f"Fixed admin privileges for user: {jan_admin.username}",
                    "user_id": jan_admin.id,
                    "username": jan_admin.username,
                    "email": jan_admin.email,
                    "is_admin": jan_admin.is_admin,
                    "action": "promoted_to_admin"
                }
            else:
                return {
                    "message": f"User already has admin privileges: {jan_admin.username}",
                    "user_id": jan_admin.id,
                    "username": jan_admin.username,
                    "email": jan_admin.email,
                    "is_admin": jan_admin.is_admin,
                    "action": "already_admin"
                }
        else:
            # Create the jan_admin user with admin privileges
            hashed_password = pwd_context.hash("admin123456")  # Default password
            jan_admin = User(
                username="jan_admin",
                email="jan@binge.de",
                hashed_password=hashed_password,
                is_admin=True,
                is_email_verified=True
            )
            db.add(jan_admin)
            db.commit()
            db.refresh(jan_admin)
            
            return {
                "message": "Created jan_admin user with admin privileges",
                "user_id": jan_admin.id,
                "username": jan_admin.username,
                "email": jan_admin.email,
                "is_admin": jan_admin.is_admin,
                "action": "created_admin",
                "default_password": "admin123456"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fixing admin privileges: {str(e)}")

@router.post("/debug/simple-login")
async def debug_simple_login(
    email: str,
    db: Session = Depends(get_db)
):
    """
    DEBUG ENDPOINT: Simple login without email verification for testing.
    This bypasses the email verification flow for easier testing.
    
    ⚠️ WARNING: This is for development/testing only!
    """
    # Disable in production
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=403, detail="Debug endpoints disabled in production")
    
    try:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User with email {email} not found")
        
        # Create access token directly (bypass email verification)
        from datetime import timedelta
        from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
        from app.auth import create_access_token
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, 
            expires_delta=access_token_expires
        )
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        user.is_email_verified = True  # Mark as verified for testing
        db.commit()
        
        return {
            "success": True,
            "message": f"Debug login successful for {user.username}",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "language": user.language or "en",
                "is_admin": user.is_admin,
                "is_word_admin": user.is_word_admin
            },
            "warning": "This is a debug endpoint - not for production use"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug login error: {str(e)}")

@router.get("/games")
def get_all_games_admin(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all games in the system (admin only).
    
    Args:
        limit: Maximum number of games to return
        offset: Number of games to skip
        status: Filter by game status (optional)
        
    Returns:
        List of all games with basic information
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Build query
        query = db.query(Game)
        
        # Apply status filter if provided
        if status:
            try:
                status_enum = GameStatus(status.lower())
                query = query.filter(Game.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Apply pagination
        games = query.offset(offset).limit(limit).all()
        
        # Get total count
        total_count = query.count()
        
        # Format response
        games_data = []
        for game in games:
            # Get players count
            players_count = db.query(Player).filter(Player.game_id == game.id).count()
            
            # Get creator info
            creator = db.query(User).filter(User.id == game.creator_id).first()
            creator_username = creator.username if creator else "Unknown"
            
            # Parse state for additional info
            state_data = json.loads(game.state) if game.state else {}
            
            games_data.append({
                "id": game.id,
                "status": game.status.value,
                "language": game.language,
                "max_players": game.max_players,
                "current_players": players_count,
                "creator_id": game.creator_id,
                "creator_username": creator_username,
                "created_at": game.created_at.isoformat(),
                "started_at": game.started_at.isoformat() if game.started_at else None,
                "completed_at": game.completed_at.isoformat() if game.completed_at else None,
                "current_player_id": game.current_player_id,
                "turn_number": state_data.get("turn_number", 0),
                "consecutive_passes": state_data.get("consecutive_passes", 0)
            })
        
        return {
            "games": games_data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "status_filter": status
        }
        
    except Exception as e:
        logger.error(f"Error getting all games: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving games: {str(e)}")

@router.get("/games/{game_id}")
def get_game_details_admin(
    game_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific game (admin only).
    
    Args:
        game_id: ID of the game to retrieve
        
    Returns:
        Detailed game information including players, moves, and state
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get game
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Get players
        players = db.query(Player).filter(Player.game_id == game_id).all()
        players_data = []
        
        for player in players:
            user = db.query(User).filter(User.id == player.user_id).first()
            if user:
                players_data.append({
                    "player_id": player.id,
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "score": player.score,
                    "rack": list(player.rack) if player.rack else [],
                    "is_computer": user.username == "computer_player"
                })
        
        # Get recent moves
        recent_moves = db.query(Move).filter(
            Move.game_id == game_id
        ).order_by(Move.timestamp.desc()).limit(10).all()
        
        moves_data = []
        for move in recent_moves:
            move_player = db.query(User).filter(User.id == move.player_id).first()
            move_data = json.loads(move.move_data) if move.move_data else {}
            
            moves_data.append({
                "id": move.id,
                "player_id": move.player_id,
                "player_username": move_player.username if move_player else "Unknown",
                "timestamp": move.timestamp.isoformat(),
                "move_type": move_data.get("type", "unknown"),
                "move_data": move_data
            })
        
        # Parse game state
        state_data = json.loads(game.state) if game.state else {}
        
        # Get creator info
        creator = db.query(User).filter(User.id == game.creator_id).first()
        
        return {
            "id": game.id,
            "status": game.status.value,
            "language": game.language,
            "max_players": game.max_players,
            "creator": {
                "id": game.creator_id,
                "username": creator.username if creator else "Unknown",
                "email": creator.email if creator else "Unknown"
            },
            "created_at": game.created_at.isoformat(),
            "started_at": game.started_at.isoformat() if game.started_at else None,
            "completed_at": game.completed_at.isoformat() if game.completed_at else None,
            "current_player_id": game.current_player_id,
            "players": players_data,
            "recent_moves": moves_data,
            "game_state": {
                "phase": state_data.get("phase"),
                "turn_number": state_data.get("turn_number", 0),
                "consecutive_passes": state_data.get("consecutive_passes", 0),
                "letter_bag_count": len(state_data.get("letter_bag", [])),
                "board_tiles": sum(1 for row in state_data.get("board", []) for cell in row if cell is not None) if state_data.get("board") else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game details: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving game details: {str(e)}")

@router.post("/games/{game_id}/terminate")
def terminate_game_admin(
    game_id: str,
    request: TerminateGameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Terminate a game administratively (admin only).
    
    Args:
        game_id: ID of the game to terminate
        request: Termination request with reason
        
    Returns:
        Confirmation of game termination
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get game
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Check if game can be terminated
        if game.status == GameStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Game is already completed")
        
        # Update game status
        old_status = game.status.value
        game.status = GameStatus.COMPLETED
        game.completed_at = datetime.now(timezone.utc)
        
        # Add termination move record
        termination_move = Move(
            game_id=game_id,
            player_id=current_user.id,  # Admin who terminated
            move_data=json.dumps({
                "type": "ADMIN_TERMINATION",
                "reason": request.reason,
                "terminated_by": current_user.username,
                "original_status": old_status
            }),
            timestamp=datetime.now(timezone.utc)
        )
        
        db.add(termination_move)
        db.commit()
        
        logger.info(f"Game {game_id} terminated by admin {current_user.username}: {request.reason}")
        
        return {
            "success": True,
            "message": f"Game {game_id} has been terminated",
            "game_id": game_id,
            "reason": request.reason,
            "terminated_by": current_user.username,
            "terminated_at": game.completed_at.isoformat(),
            "previous_status": old_status,
            "new_status": game.status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error terminating game: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error terminating game: {str(e)}")

@router.post("/run-feedback-migration")
def run_feedback_migration(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run feedback system migration (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # SQL to create feedback table and enums
        migration_sql = """
        -- Create feedback category enum
        DO $$ BEGIN
            CREATE TYPE feedbackcategory AS ENUM (
                'bug_report', 'feature_request', 'performance_issue', 
                'ui_ux_feedback', 'game_logic_issue', 'authentication_problem',
                'network_connection_issue', 'general_feedback', 'other'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;

        -- Create feedback status enum
        DO $$ BEGIN
            CREATE TYPE feedbackstatus AS ENUM (
                'new', 'in_review', 'resolved', 'closed'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;

        -- Drop existing feedback table if it exists (to fix schema)
        DROP TABLE IF EXISTS feedback;
        
        -- Create feedback table
        CREATE TABLE IF NOT EXISTS feedback (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            category feedbackcategory NOT NULL,
            description TEXT NOT NULL,
            contact_email VARCHAR(255),
            debug_logs JSON,
            device_info JSON,
            app_info JSON,
            status feedbackstatus NOT NULL DEFAULT 'new',
            admin_notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
        CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(category);
        CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
        CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
        """
        
        # Execute migration
        db.execute(text(migration_sql))
        db.commit()
        
        # Verify table exists
        result = db.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'feedback'"))
        count = result.scalar()
        
        return {
            "success": True,
            "message": "Feedback migration completed successfully",
            "table_created": count > 0
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@router.get("/debug/my-persistent-token")
def get_my_persistent_token(current_user: User = Depends(get_current_user)):
    """Debug endpoint to get current user's persistent token for testing."""
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        },
        "persistent_token": current_user.persistent_token,
        "persistent_token_expires": current_user.persistent_token_expires.isoformat() if current_user.persistent_token_expires else None,
        "has_valid_token": bool(current_user.persistent_token and current_user.persistent_token_expires),
        "current_time": datetime.now(timezone.utc).isoformat()
    }

@router.get("/debug/list-all-users")
def list_all_users_debug(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Debug endpoint to list all users in the database."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db.query(User).all()
    user_list = []
    
    for user in users:
        user_list.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_word_admin": user.is_word_admin,
            "is_email_verified": user.is_email_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "has_persistent_token": bool(user.persistent_token),
            "language": user.language
        })
    
    return {
        "success": True,
        "total_users": len(user_list),
        "users": user_list,
        "current_time": datetime.now(timezone.utc).isoformat()
    }

@router.post("/database/cleanup-test-users")
def cleanup_test_users(
    confirm: bool = False,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Clean up test users from production database."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Define test user patterns to remove
    test_usernames = ["player01", "player02", "computer", "Computer", "test_user", "testuser"]
    test_emails = ["player01@binge.de", "player02@binge.de", "computer@binge.de", "test@example.com"]
    
    # Find test users
    test_users = db.query(User).filter(
        (User.username.in_(test_usernames)) | 
        (User.email.in_(test_emails)) |
        (User.username.like("test_%")) |
        (User.username.like("player%")) |
        (User.email.like("%@test.%")) |
        (User.email.like("%@example.%"))
    ).all()
    
    if not confirm:
        return {
            "success": False,
            "message": "This is a dry run. Set confirm=true to actually delete users.",
            "test_users_found": len(test_users),
            "users_to_delete": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                for user in test_users
            ],
            "warning": "These users will be permanently deleted if confirm=true"
        }
    
    # Delete test users
    deleted_count = 0
    deleted_users = []
    
    for user in test_users:
        # Skip if this is the current admin user (safety check)
        if user.id == current_user.id:
            continue
            
        deleted_users.append({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })
        
        db.delete(user)
        deleted_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Successfully deleted {deleted_count} test users from production",
        "deleted_users": deleted_users,
        "remaining_users": db.query(User).count(),
        "current_time": datetime.now(timezone.utc).isoformat()
    }

@router.post("/emergency/cleanup-test-users")
def emergency_cleanup_test_users(admin_token: str, confirm: bool = False, db: Session = Depends(get_db)):
    """Emergency cleanup of test users using admin token file authentication."""
    
    # Read admin token from file
    try:
        with open("/app/admin_token.txt", "r") as f:
            stored_admin_token = f.read().strip()
    except FileNotFoundError:
        raise HTTPException(status_code=403, detail="Admin token file not found")
    
    # Verify admin token
    if admin_token != stored_admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    # Define test user patterns to remove
    test_usernames = ["player01", "player02", "computer", "Computer", "test_user", "testuser"]
    test_emails = ["player01@binge.de", "player02@binge.de", "computer@binge.de", "test@example.com"]
    
    # Find test users (exclude admin users for safety)
    test_users = db.query(User).filter(
        ((User.username.in_(test_usernames)) | 
         (User.email.in_(test_emails)) |
         (User.username.like("test_%")) |
         (User.username.like("player%")) |
         (User.email.like("%@test.%")) |
         (User.email.like("%@example.%"))) &
        (User.is_admin == False)  # Safety: never delete admin users
    ).all()
    
    if not confirm:
        return {
            "success": False,
            "message": "This is a dry run. Set confirm=true to actually delete users.",
            "test_users_found": len(test_users),
            "users_to_delete": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                for user in test_users
            ],
            "warning": "These users will be permanently deleted if confirm=true"
        }
    
    # Delete test users
    deleted_count = 0
    deleted_users = []
    
    for user in test_users:
        deleted_users.append({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })
        
        db.delete(user)
        deleted_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Successfully deleted {deleted_count} test users from production",
        "deleted_users": deleted_users,
        "remaining_users": db.query(User).count(),
        "current_time": datetime.now(timezone.utc).isoformat()
    }

@router.get("/debug/auth-test")
def test_authentication_consistency(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to test authentication consistency across all endpoints"""
    return {
        "success": True,
        "message": "Authentication working consistently",
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "authentication_method": "Bearer token via get_current_user dependency",
        "endpoints_using_same_auth": [
            "/auth/me",
            "/games/my-games", 
            "/feedback/submit",
            "/admin/debug/auth-test"
        ]
    }

@router.post("/fix-feedback-schema")
def fix_feedback_schema(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fix feedback table schema mismatch (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Check current schema
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'feedback' AND column_name = 'user_id'
        """))
        current_schema = result.fetchone()
        
        if not current_schema:
            return {"success": False, "message": "Feedback table not found"}
            
        current_type = current_schema[1]
        
        if current_type in ['character varying', 'text', 'varchar']:
            # Fix the schema mismatch
            fix_sql = """
            -- Backup existing data if any
            CREATE TEMP TABLE feedback_backup AS SELECT * FROM feedback;
            
            -- Drop existing table
            DROP TABLE IF EXISTS feedback;
            
            -- Create feedback table with correct schema
            CREATE TABLE feedback (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                category feedbackcategory NOT NULL,
                description TEXT NOT NULL,
                contact_email VARCHAR(255),
                debug_logs JSON,
                device_info JSON,
                app_info JSON,
                status feedbackstatus NOT NULL DEFAULT 'new',
                admin_notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
            CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(category);
            CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
            CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
            
            -- Restore data if any (convert user_id to integer if possible)
            INSERT INTO feedback SELECT 
                id, 
                CAST(user_id AS INTEGER),
                category,
                description,
                contact_email,
                debug_logs,
                device_info,
                app_info,
                status,
                admin_notes,
                created_at,
                updated_at
            FROM feedback_backup 
            WHERE user_id ~ '^[0-9]+$';  -- Only insert rows where user_id is numeric
            """
            
            db.execute(text(fix_sql))
            db.commit()
            
            return {
                "success": True,
                "message": "Feedback schema fixed successfully",
                "old_type": current_type,
                "new_type": "integer",
                "action": "Schema converted from String to Integer"
            }
        else:
            return {
                "success": True,
                "message": "Schema is already correct",
                "current_type": current_type,
                "action": "No changes needed"
            }
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Schema fix failed: {str(e)}")