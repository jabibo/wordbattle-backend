from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import WordList
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quick-fix", tags=["quick-fix"])

@router.post("/add-german-words")
def add_essential_german_words(db: Session = Depends(get_db)):
    """
    Quick fix to add essential German words including RAND.
    This is a one-time fix for the secure production environment.
    """
    
    essential_words = [
        "RAND", "HALLO", "WELT", "WORT", "BAUM", "HAUS", "AUTO", "TISCH", "STUHL", 
        "DEUTSCH", "BRIEF", "BUCH", "STADT", "LAND", "HAND", "KIND", "MANN", "FRAU", 
        "GELD", "ZEIT", "ARBEIT", "LEBEN", "WASSER", "FEUER", "LUFT", "ERDE", "SONNE", 
        "MOND", "STERN", "HIMMEL", "BERG", "TAL", "FLUSS", "MEER", "STRAND", "WALD", 
        "FELD", "GARTEN", "BLUME", "TIER", "HUND", "KATZE", "PFERD", "VOGEL", "FISCH", 
        "BROT", "MILCH", "KÄSE", "FLEISCH", "OBST", "GEMÜSE", "GRÜN", "BLAU", "ROT", 
        "GELB", "SCHWARZ", "WEISS", "GROSS", "KLEIN", "ALT", "NEU", "GUT", "SCHLECHT",
        "SCHNELL", "LANGSAM", "HEISS", "KALT", "HELL", "DUNKEL", "LAUT", "LEISE",
        "STARK", "SCHWACH", "REICH", "ARM", "JUNG", "MÜDE", "WACH", "GLÜCKLICH",
        "TRAURIG", "KOMMEN", "GEHEN", "SEHEN", "HÖREN", "SPRECHEN", "ESSEN", "TRINKEN",
        "SCHLAFEN", "ARBEITEN", "SPIELEN", "LESEN", "SCHREIBEN", "FAHREN", "LAUFEN",
        "HEUTE", "GESTERN", "MORGEN", "JAHR", "MONAT", "WOCHE", "STUNDE", "MINUTE",
        "HIER", "DORT", "OBEN", "UNTEN", "LINKS", "RECHTS", "INNEN", "AUSSEN",
        "TEST", "SPIEL", "TAG", "TAGE", "ÜBER", "SCHÖN"
    ]
    
    try:
        # Count existing words
        existing_count = db.query(WordList).filter(WordList.language == "de").count()
        logger.info(f"🔍 Current German words in database: {existing_count}")
        
        # Add new words (check for duplicates)
        added_count = 0
        for word in essential_words:
            existing = db.query(WordList).filter(
                WordList.word == word, 
                WordList.language == "de"
            ).first()
            
            if not existing:
                db.add(WordList(word=word, language="de"))
                added_count += 1
                logger.info(f"✅ Added word: {word}")
            else:
                logger.info(f"ℹ️  Word already exists: {word}")
        
        db.commit()
        
        # Get final count
        final_count = db.query(WordList).filter(WordList.language == "de").count()
        
        logger.info(f"🎉 Word import completed! Added {added_count} new words")
        
        return {
            "success": True,
            "message": f"Successfully added {added_count} German words",
            "words_before": existing_count,
            "words_added": added_count,
            "words_after": final_count,
            "sample_words": ["RAND", "HALLO", "WELT", "SPIEL", "HAUS"]
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error adding words: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add words: {str(e)}")

@router.get("/check-words")
def check_word_status(db: Session = Depends(get_db)):
    """Check status of German words in the database."""
    
    test_words = ["RAND", "HALLO", "WELT", "SPIEL", "HAUS"]
    results = {}
    
    for word in test_words:
        exists = db.query(WordList).filter(
            WordList.word == word, 
            WordList.language == "de"
        ).first() is not None
        results[word] = exists
    
    total_count = db.query(WordList).filter(WordList.language == "de").count()
    
    return {
        "total_german_words": total_count,
        "test_words": results,
        "all_test_words_exist": all(results.values())
    }
