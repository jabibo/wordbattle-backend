from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.auth import get_current_user
from app.models import User, WordList
from app.wordlist import import_wordlist, load_wordlist_from_file
import os
import tempfile

router = APIRouter(prefix="/admin", tags=["admin"])

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