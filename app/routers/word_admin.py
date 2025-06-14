from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.auth import get_current_user
from app.models import User, WordList
from datetime import datetime, timezone
import io
import csv
import logging
from sqlalchemy import text, or_
from app.utils.wordlist_utils import clear_wordlist_cache, add_word_to_database, add_words_to_database, get_cache_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/word-admin", tags=["word-admin"])

class AddWordRequest(BaseModel):
    word: str
    language: str

class AddWordsRequest(BaseModel):
    words: List[str]
    language: str

class WordAdminStatusRequest(BaseModel):
    user_id: int
    is_word_admin: bool

def require_word_admin(current_user = Depends(get_current_user)):
    """Require the current user to be a word admin or regular admin."""
    if not current_user.is_word_admin and not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Word admin or admin privileges required"
        )
    return current_user

def require_admin(current_user = Depends(get_current_user)):
    """Require the current user to be a regular admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return current_user

@router.get("/status")
def get_word_admin_status(
    current_user = Depends(get_current_user)
):
    """Get the current user's word admin status and capabilities."""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "is_word_admin": current_user.is_word_admin,
        "can_manage_words": current_user.is_word_admin or current_user.is_admin
    }

@router.post("/add-word")
def add_single_word(
    request: AddWordRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_word_admin)
):
    """Add a single word to the wordlist with automatic cache invalidation."""
    word = request.word.strip()
    language = request.language.lower()
    
    if not word:
        raise HTTPException(status_code=400, detail="Word cannot be empty")
    
    if not language:
        raise HTTPException(status_code=400, detail="Language cannot be empty")
    
    # Use the cache-aware function
    was_added = add_word_to_database(word, language, current_user.id, db)
    
    if not was_added:
        raise HTTPException(
            status_code=409,
            detail=f"Word '{word.upper()}' already exists in {language} wordlist"
        )
    
    return {
        "message": f"Word '{word.upper()}' added successfully to {language} wordlist",
        "word": {
            "word": word.upper(),
            "language": language,
            "added_by": current_user.username,
            "cache_cleared": True
        }
    }

@router.post("/add-words")
def add_multiple_words(
    request: AddWordsRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_word_admin)
):
    """Add multiple words to the wordlist with automatic cache invalidation."""
    language = request.language.lower()
    words = request.words
    
    if not words:
        raise HTTPException(status_code=400, detail="No words provided")
    
    if not language:
        raise HTTPException(status_code=400, detail="Language cannot be empty")
    
    # Use the cache-aware function
    result = add_words_to_database(words, language, current_user.id, db)
    
    if result["newly_added"] == 0:
        return {
            "message": "All words already exist in the wordlist",
            **result,
            "cache_cleared": False
        }
    
    return {
        "message": f"Successfully added {result['newly_added']} words to {language} wordlist",
        **result,
        "cache_cleared": True
    }

@router.post("/upload-wordlist")
async def upload_wordlist(
    language: str = Body(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_word_admin)
):
    """Upload a wordlist file and add all words to the database with automatic cache invalidation."""
    language = language.lower()
    
    if not file.filename.endswith(('.txt', '.csv')):
        raise HTTPException(
            status_code=400,
            detail="File must be a .txt or .csv file"
        )
    
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8-sig')  # Handle BOM
        
        # Parse words from file
        words = []
        if file.filename.endswith('.csv'):
            # Parse CSV (assume first column contains words)
            csv_reader = csv.reader(io.StringIO(text_content))
            for row in csv_reader:
                if row and row[0].strip():
                    words.append(row[0].strip())
        else:
            # Parse plain text (one word per line)
            for line in text_content.split('\n'):
                word = line.strip()
                if word:
                    words.append(word)
        
        if not words:
            raise HTTPException(status_code=400, detail="No valid words found in file")
        
        # Use the cache-aware function
        result = add_words_to_database(words, language, current_user.id, db)
        
        return {
            "message": f"Successfully processed file '{file.filename}'",
            "filename": file.filename,
            **result,
            "cache_cleared": result["newly_added"] > 0
        }
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File encoding not supported. Please use UTF-8 encoding."
        )
    except Exception as e:
        logger.error(f"Error uploading wordlist: {e}")
        raise HTTPException(status_code=500, detail="Error processing file")

@router.get("/cache-stats")
def get_dictionary_cache_stats(
    current_user = Depends(require_word_admin)
):
    """Get statistics about the current dictionary cache state."""
    stats = get_cache_stats()
    return {
        "cache_stats": stats,
        "message": "Dictionary cache statistics"
    }

@router.post("/clear-cache")
def clear_dictionary_cache(
    language: str = None,
    current_user = Depends(require_word_admin)
):
    """Manually clear the dictionary cache for a language or all languages."""
    clear_wordlist_cache(language)
    
    if language:
        return {
            "message": f"Dictionary cache cleared for language: {language}",
            "language": language
        }
    else:
        return {
            "message": "All dictionary caches cleared"
        }

@router.get("/download-wordlist/{language}")
def download_wordlist(
    language: str,
    format: str = "txt",  # txt or csv
    db: Session = Depends(get_db),
    current_user = Depends(require_word_admin)
):
    """Download the complete wordlist for a language."""
    language = language.lower()
    format = format.lower()
    
    if format not in ["txt", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be 'txt' or 'csv'")
    
    # Get all words for the language
    words_query = db.query(WordList).filter(WordList.language == language).order_by(WordList.word)
    words = words_query.all()
    
    if not words:
        raise HTTPException(status_code=404, detail=f"No words found for language: {language}")
    
    # Create file content
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Word", "Added By", "Added Date"])  # Header
        for word_obj in words:
            added_by = word_obj.added_by_user.username if word_obj.added_by_user else "System"
            added_date = word_obj.added_timestamp.strftime("%Y-%m-%d %H:%M:%S") if word_obj.added_timestamp else "Unknown"
            writer.writerow([word_obj.word, added_by, added_date])
        content = output.getvalue()
        media_type = "text/csv"
        filename = f"wordlist_{language}.csv"
    else:
        # Plain text format
        content = "\n".join([word_obj.word for word_obj in words])
        media_type = "text/plain"
        filename = f"wordlist_{language}.txt"
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/wordlist-stats")
def get_wordlist_stats(
    db: Session = Depends(get_db),
    current_user = Depends(require_word_admin)
):
    """Get statistics about wordlists."""
    try:
        # Get stats by language using standard SQL
        language_stats = db.execute(text("""
            SELECT 
                language,
                COUNT(*) as total_words,
                COUNT(added_user_id) as user_added_words,
                COUNT(CASE WHEN added_user_id IS NULL THEN 1 END) as system_words
            FROM wordlists 
            GROUP BY language
            ORDER BY language
        """)).fetchall()
        
        # Get top contributors using standard SQL (no array_agg)
        top_contributors = db.execute(text("""
            SELECT 
                u.username,
                COUNT(w.id) as words_added
            FROM wordlists w
            JOIN users u ON w.added_user_id = u.id
            GROUP BY u.id, u.username
            ORDER BY words_added DESC
            LIMIT 10
        """)).fetchall()
        
        # Get recent additions
        recent_additions = db.query(WordList).filter(
            WordList.added_user_id.isnot(None)
        ).order_by(WordList.added_timestamp.desc()).limit(20).all()
        
        return {
            "language_stats": [
                {
                    "language": stat[0],
                    "total_words": stat[1],
                    "user_added": stat[2],
                    "system_words": stat[3]
                }
                for stat in language_stats
            ],
            "top_contributors": [
                {
                    "username": contrib[0],
                    "words_added": contrib[1],
                    "languages": []  # Simplified for compatibility
                }
                for contrib in top_contributors
            ],
            "recent_additions": [
                {
                    "word": word.word,
                    "language": word.language,
                    "added_by": word.added_by_user.username if word.added_by_user else "System",
                    "added_timestamp": word.added_timestamp.isoformat() if word.added_timestamp else None
                }
                for word in recent_additions
            ]
        }
    except Exception as e:
        logger.error(f"Error getting wordlist stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# Admin-only endpoints for managing word admin privileges

@router.post("/grant-word-admin")
def grant_word_admin_privilege(
    request: WordAdminStatusRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Grant or revoke word admin privileges (admin only)."""
    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    target_user.is_word_admin = request.is_word_admin
    db.commit()
    
    action = "granted" if request.is_word_admin else "revoked"
    logger.info(f"Admin {current_user.username} {action} word admin privileges for {target_user.username}")
    
    return {
        "message": f"Word admin privileges {action} for user {target_user.username}",
        "user": {
            "id": target_user.id,
            "username": target_user.username,
            "is_admin": target_user.is_admin,
            "is_word_admin": target_user.is_word_admin
        }
    }

@router.get("/list-word-admins")
def list_word_admins(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """List all users with word admin privileges (admin only)."""
    word_admins = db.query(User).filter(User.is_word_admin == True).all()
    
    return {
        "word_admins": [
            {
                "id": admin.id,
                "username": admin.username,
                "email": admin.email,
                "is_admin": admin.is_admin,
                "created_at": admin.created_at.isoformat() if admin.created_at else None
            }
            for admin in word_admins
        ],
        "total_count": len(word_admins)
    } 