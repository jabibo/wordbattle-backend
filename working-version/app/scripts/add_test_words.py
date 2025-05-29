from app.database import SessionLocal
from app.models import WordList

# Connect to the database
db = SessionLocal()

try:
    # Add English test words
    en_words = [
        WordList(word="SCRABBLE", language="en"),
        WordList(word="GAME", language="en"),
        WordList(word="WORD", language="en"),
        WordList(word="TEST", language="en"),
        WordList(word="PLAY", language="en")
    ]
    
    # Check if words already exist
    existing = db.query(WordList).filter(WordList.language == "en").count()
    if existing == 0:
        db.add_all(en_words)
        db.commit()
        print(f"Added {len(en_words)} English words to the database")
    else:
        print(f"English words already exist in the database ({existing} words)")
    
    # Add German test words if needed
    de_count = db.query(WordList).filter(WordList.language == "de").count()
    if de_count == 0:
        de_words = [
            WordList(word="HALLO", language="de"),
            WordList(word="WELT", language="de"),
            WordList(word="SPIEL", language="de"),
            WordList(word="WORT", language="de"),
            WordList(word="TEST", language="de")
        ]
        db.add_all(de_words)
        db.commit()
        print(f"Added {len(de_words)} German words to the database")
    else:
        print(f"German words already exist in the database ({de_count} words)")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
