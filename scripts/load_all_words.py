#!/usr/bin/env python3
"""
Script to load all remaining words into the test database.
This script will load all German words that haven't been loaded yet.
"""

import os
import sys

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database_manager import check_database_status, load_wordlist
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Load all remaining words into the database."""
    
    # Check current status
    logger.info("Checking current database status...")
    status = check_database_status()
    
    current_de = status["word_counts"].get("de", 0)
    current_en = status["word_counts"].get("en", 0)
    
    logger.info(f"Current word counts: DE={current_de}, EN={current_en}")
    
    # Load remaining German words
    if current_de < 600000:  # We know there are ~601,565 total
        logger.info(f"Loading remaining German words starting from {current_de}...")
        
        # Load in chunks to avoid memory issues
        chunk_size = 50000
        total_loaded = 0
        
        while current_de + total_loaded < 600000:
            skip = current_de + total_loaded
            logger.info(f"Loading German words: skip={skip}, limit={chunk_size}")
            
            result = load_wordlist(
                language="de", 
                skip=skip, 
                limit=chunk_size
            )
            
            if not result["success"]:
                logger.error(f"Failed to load words: {result.get('error')}")
                break
                
            words_loaded = result.get("words_loaded", 0)
            total_loaded += words_loaded
            
            logger.info(f"Loaded {words_loaded} words. Total loaded this session: {total_loaded}")
            
            if words_loaded < chunk_size:
                # We've reached the end of available words
                logger.info("Reached end of available words")
                break
        
        logger.info(f"Finished loading German words. Total loaded: {total_loaded}")
    else:
        logger.info("German words already fully loaded")
    
    # Check if English needs loading
    if current_en < 170000:  # We know there are ~178,690 total
        logger.info("Loading remaining English words...")
        result = load_wordlist(
            language="en", 
            skip=current_en, 
            limit=200000  # Load all remaining
        )
        
        if result["success"]:
            logger.info(f"Loaded {result.get('words_loaded', 0)} English words")
        else:
            logger.error(f"Failed to load English words: {result.get('error')}")
    else:
        logger.info("English words already fully loaded")
    
    # Final status check
    logger.info("Final status check...")
    final_status = check_database_status()
    final_de = final_status["word_counts"].get("de", 0)
    final_en = final_status["word_counts"].get("en", 0)
    
    logger.info(f"Final word counts: DE={final_de}, EN={final_en}")
    logger.info("Word loading completed!")

if __name__ == "__main__":
    main() 