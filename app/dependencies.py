from fastapi import Depends
from app.auth import get_current_user
from app.utils.i18n import TranslationHelper
from app.models.user import User
from app.db import get_db  # Import from new location

def get_translation_helper(current_user: User = Depends(get_current_user)) -> TranslationHelper:
    """
    Get a translation helper configured for the current user's language preference.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        TranslationHelper instance configured for the user's language
    """
    user_language = getattr(current_user, 'language', 'en') or 'en'
    return TranslationHelper(user_language)
