#!/usr/bin/env python3
"""
Quick fix to add essential German words to the secure production database.
This connects directly to the database and adds words.
"""

import os
import sys
import psycopg2
from typing import List

# Database connection details for secure production
DB_CONFIG = {
    'host': '35.240.110.171',  # Public IP of secure production database
    'port': 5432,
    'dbname': 'wordbattle_prod',
    'user': 'wordbattle',
    'password': 'HKrzBR4nMpF4ddgf'
}

# Essential German words to add (including RAND)
ESSENTIAL_WORDS = [
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
    "HEUTE", "GESTERN", "MORGEN", "JAHR", "MONAT", "WOCHE", "TAG", "STUNDE",
    "MINUTE", "HIER", "DORT", "OBEN", "UNTEN", "LINKS", "RECHTS", "INNEN", "AUSSEN"
]

def connect_to_database():
    """Connect to the secure production database."""
    try:
        print("🔌 Connecting to secure production database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected successfully")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def check_existing_words(conn) -> int:
    """Check how many German words already exist."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM words WHERE language = 'de'")
            count = cur.fetchone()[0]
            print(f"📊 Current German words in database: {count}")
            return count
    except Exception as e:
        print(f"❌ Error checking existing words: {e}")
        return 0

def add_words_to_database(conn, words: List[str]) -> int:
    """Add words to the database."""
    added_count = 0
    try:
        with conn.cursor() as cur:
            for word in words:
                try:
                    # Check if word already exists
                    cur.execute("SELECT COUNT(*) FROM words WHERE word = %s AND language = 'de'", (word,))
                    if cur.fetchone()[0] == 0:
                        # Add the word
                        cur.execute("INSERT INTO words (word, language) VALUES (%s, 'de')", (word,))
                        added_count += 1
                        print(f"✅ Added: {word}")
                    else:
                        print(f"ℹ️  Already exists: {word}")
                except Exception as e:
                    print(f"❌ Error adding {word}: {e}")
            
            conn.commit()
            print(f"💾 Committed {added_count} new words to database")
            return added_count
            
    except Exception as e:
        print(f"❌ Error during batch insert: {e}")
        conn.rollback()
        return 0

def test_words(conn, test_words: List[str]):
    """Test that words were added successfully."""
    print("\n🧪 Testing added words...")
    try:
        with conn.cursor() as cur:
            for word in test_words:
                cur.execute("SELECT COUNT(*) FROM words WHERE word = %s AND language = 'de'", (word,))
                if cur.fetchone()[0] > 0:
                    print(f"✅ {word} found in database")
                else:
                    print(f"❌ {word} NOT found in database")
    except Exception as e:
        print(f"❌ Error testing words: {e}")

def main():
    print("🚀 Quick German Word Fix for Secure Production")
    print("=" * 50)
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        sys.exit(1)
    
    try:
        # Check existing words
        existing_count = check_existing_words(conn)
        
        # Add essential words
        print(f"\n📤 Adding {len(ESSENTIAL_WORDS)} essential German words...")
        added_count = add_words_to_database(conn, ESSENTIAL_WORDS)
        
        print(f"\n📊 Summary:")
        print(f"   - Words before: {existing_count}")
        print(f"   - Words added: {added_count}")
        print(f"   - Total words now: {existing_count + added_count}")
        
        # Test key words
        test_words = ["RAND", "HALLO", "WELT", "SPIEL"]
        test_words(conn, test_words)
        
        print(f"\n🎉 Word import completed!")
        print(f"You should now be able to play RAND and other common German words.")
        
    finally:
        conn.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    main()
