#!/usr/bin/env python3
"""
Load German words directly into Google Cloud SQL database
"""
import psycopg2
from psycopg2.extras import execute_batch
import sys

# Database connection details
DB_HOST = "35.187.90.105"
DB_PORT = "5432"
DB_NAME = "wordbattle_db"
DB_USER = "postgres"
DB_PASSWORD = "wordbattle_password"

def load_words():
    """Load German words from file into database"""
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Check current word count
        cursor.execute("SELECT COUNT(*) FROM wordlists WHERE language = 'de'")
        current_count = cursor.fetchone()[0]
        print(f"Current German words in database: {current_count}")
        
        # Read words from file
        print("Reading words from file...")
        with open('data/de_words.txt', 'r', encoding='utf-8') as f:
            words = [line.strip().upper() for line in f if line.strip()]
        
        print(f"Found {len(words)} words in file")
        
        # Prepare data for insertion (avoid duplicates)
        print("Preparing words for insertion...")
        word_data = [(word, 'de') for word in words]
        
        # Insert words in batches
        print("Inserting words into database...")
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(word_data), batch_size):
            batch = word_data[i:i + batch_size]
            try:
                execute_batch(
                    cursor,
                    "INSERT INTO wordlists (word, language) VALUES (%s, %s) ON CONFLICT (word, language) DO NOTHING",
                    batch,
                    page_size=batch_size
                )
                total_inserted += len(batch)
                if total_inserted % 10000 == 0:
                    print(f"Inserted {total_inserted} words...")
                    conn.commit()
            except Exception as e:
                print(f"Error inserting batch: {e}")
                conn.rollback()
        
        # Final commit
        conn.commit()
        
        # Check final count
        cursor.execute("SELECT COUNT(*) FROM wordlists WHERE language = 'de'")
        final_count = cursor.fetchone()[0]
        
        print(f"Final German words in database: {final_count}")
        print(f"Words added: {final_count - current_count}")
        
        cursor.close()
        conn.close()
        
        print("✅ Word loading completed successfully!")
        
    except Exception as e:
        print(f"❌ Error loading words: {e}")
        sys.exit(1)

if __name__ == "__main__":
    load_words() 