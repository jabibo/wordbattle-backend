#!/usr/bin/env python3
"""
Direct database update script to change test user emails to @binge.de format.
This provides immediate functionality while we continue working on deployment issues.
"""

import os
import psycopg2
from datetime import datetime

# Database connection parameters
DB_HOST = "wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com"
DB_NAME = "wordbattle"
DB_USER = "postgres"
DB_PASSWORD = "Wordbattle2024"

def update_user_emails():
    """Update test user emails to @binge.de format"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # First, let's see what users exist
        cursor.execute("SELECT id, username, email FROM users ORDER BY id LIMIT 10")
        users = cursor.fetchall()
        
        print("\nCurrent users:")
        for user_id, username, email in users:
            print(f"  ID: {user_id}, Username: {username}, Email: {email}")
        
        # Find the test users that are currently being used for tokens
        cursor.execute("SELECT id, username, email FROM users WHERE username LIKE 'testuser_%' ORDER BY id LIMIT 2")
        test_users = cursor.fetchall()
        
        if len(test_users) >= 2:
            user1 = test_users[0]
            user2 = test_users[1]
            
            print(f"\nUpdating emails for test users:")
            print(f"  User 1: {user1[1]} -> player01@binge.de")
            print(f"  User 2: {user2[1]} -> player02@binge.de")
            
            # Update the emails
            cursor.execute("UPDATE users SET email = %s WHERE id = %s", ("player01@binge.de", user1[0]))
            cursor.execute("UPDATE users SET email = %s WHERE id = %s", ("player02@binge.de", user2[0]))
            
            # Commit the changes
            conn.commit()
            
            print("✅ Email updates completed successfully!")
            
            # Verify the changes
            cursor.execute("SELECT id, username, email FROM users WHERE id IN (%s, %s)", (user1[0], user2[0]))
            updated_users = cursor.fetchall()
            
            print("\nVerification - Updated users:")
            for user_id, username, email in updated_users:
                print(f"  ID: {user_id}, Username: {username}, Email: {email}")
                
        else:
            print("❌ Could not find enough test users to update")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        if 'conn' in locals():
            conn.close()
            print("\nDatabase connection closed")

if __name__ == "__main__":
    print("WordBattle Email Update Script")
    print("=" * 40)
    print(f"Timestamp: {datetime.now()}")
    print(f"Target: {DB_HOST}/{DB_NAME}")
    print()
    
    update_user_emails() 