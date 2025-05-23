#!/usr/bin/env python
"""
Script to import wordlists into the database.
"""

import os
import sys
import argparse
from app.wordlist import import_wordlist

def main():
    parser = argparse.ArgumentParser(description="Import wordlists into the database")
    parser.add_argument("language", help="Language code (e.g., 'de', 'en')")
    parser.add_argument("--path", help="Path to wordlist file")
    
    args = parser.parse_args()
    
    if args.path and not os.path.exists(args.path):
        print(f"Error: File not found: {args.path}")
        return 1
    
    try:
        import_wordlist(args.language, args.path)
        return 0
    except Exception as e:
        print(f"Error importing wordlist: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())