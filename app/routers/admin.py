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