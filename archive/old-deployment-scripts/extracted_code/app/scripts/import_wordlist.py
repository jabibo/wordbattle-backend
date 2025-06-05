#!/usr/bin/env python
"""
Script to import wordlists into the database.
"""

import os
import sys
import argparse

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.wordlist import import_wordlist
from app.database import SessionLocal
from app.models.wordlist import WordList

def main():
    parser = argparse.ArgumentParser(description="Import wordlists into the database")
    parser.add_argument("language", help="Language code (e.g., 'de', 'en')")
    parser.add_argument("--path", help="Path to wordlist file")
    parser.add_argument("--force", action="store_true", help="Force reimport even if language already exists")
    
    args = parser.parse_args()
    
    if args.path and not os.path.exists(args.path):
        print(f"Error: File not found: {args.path}")
        return 1
    
    try:
        # If force is specified, delete existing words for this language
        if args.force:
            db = SessionLocal()
            try:
                count = db.query(WordList).filter(WordList.language == args.language).count()
                if count > 0:
                    print(f"Deleting {count} existing words for language '{args.language}'")
                    db.query(WordList).filter(WordList.language == args.language).delete()
                    db.commit()
            finally:
                db.close()
        
        import_wordlist(args.language, args.path)
        return 0
    except Exception as e:
        print(f"Error importing wordlist: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
