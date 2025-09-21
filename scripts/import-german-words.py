#!/usr/bin/env python3
"""
Import German words to the secure production database.
This script reads from the local de_words.txt file and imports words via the backend API.
"""

import requests
import os
import sys
import time
from typing import List

# Configuration
BACKEND_URL = "https://wordbattle-backend-prod-15814336315.europe-west1.run.app"
WORD_FILE = "data/de_words.txt"
BATCH_SIZE = 1000  # Import words in batches
MAX_WORDS = 50000  # Limit to avoid timeout

def load_words_from_file(file_path: str, max_words: int = None) -> List[str]:
    """Load words from the German word file."""
    print(f"📖 Loading words from {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"❌ Word file not found: {file_path}")
        return []
    
    words = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if max_words and i >= max_words:
                break
            word = line.strip().upper()
            if word and len(word) >= 2:  # Only words with 2+ characters
                words.append(word)
    
    print(f"✅ Loaded {len(words)} words from file")
    return words

def import_words_batch(words: List[str], token: str) -> bool:
    """Import a batch of words via the backend API."""
    url = f"{BACKEND_URL}/admin/words/import"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "language": "de",
        "words": words
    }
    
    try:
        print(f"📤 Importing batch of {len(words)} words...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully imported {result.get('imported', len(words))} words")
            return True
        else:
            print(f"❌ Import failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during import: {e}")
        return False

def get_admin_token() -> str:
    """Get admin token for API access."""
    print("🔑 Please provide an admin token for the secure production backend.")
    print("You can get this from your Flutter app after logging in as an admin.")
    print("Look for the token in the logs when you log in.")
    print()
    
    token = input("Enter admin token: ").strip()
    if not token:
        print("❌ No token provided")
        sys.exit(1)
    
    return token

def main():
    print("🚀 German Word Import Script for Secure Production")
    print("=" * 50)
    
    # Load words from file
    words = load_words_from_file(WORD_FILE, MAX_WORDS)
    if not words:
        print("❌ No words to import")
        sys.exit(1)
    
    # Get admin token
    token = get_admin_token()
    
    print(f"📊 Plan: Import {len(words)} words in batches of {BATCH_SIZE}")
    input("Press Enter to start import...")
    
    # Import words in batches
    total_imported = 0
    total_batches = (len(words) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(words), BATCH_SIZE):
        batch_num = (i // BATCH_SIZE) + 1
        batch = words[i:i + BATCH_SIZE]
        
        print(f"\n📦 Batch {batch_num}/{total_batches}")
        
        if import_words_batch(batch, token):
            total_imported += len(batch)
            print(f"✅ Progress: {total_imported}/{len(words)} words imported")
        else:
            print(f"❌ Batch {batch_num} failed, stopping import")
            break
        
        # Small delay between batches
        if batch_num < total_batches:
            time.sleep(1)
    
    print(f"\n🎉 Import completed! Total words imported: {total_imported}")
    
    # Test a few words
    print("\n🧪 Testing imported words...")
    test_words = ["RAND", "HALLO", "WELT", "SPIEL", "HAUS"]
    for word in test_words:
        if word in words:
            print(f"✅ {word} should now be available")

if __name__ == "__main__":
    main()

