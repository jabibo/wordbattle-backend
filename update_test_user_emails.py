#!/usr/bin/env python3
"""
Script to update test user emails to @binge.de format
This updates the database directly without changing application code
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection parameters
DB_HOST = "wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com"
DB_NAME = "wordbattle"
DB_USER = "postgres"
DB_PASSWORD = "Wordbattle2024"
DB_PORT = "5432"

def update_test_user_emails():
    """Update test user emails to @binge.de format"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Email mapping for the actual users currently being used
        # Using testuser01 and testuser02 to avoid conflicts
        email_updates = {
            "testuser_80cb46b1": "testuser01@binge.de",
            "testuser_48a04d07_1": "testuser02@binge.de"
        }
        
        for username, new_email in email_updates.items():
            # Check if user exists
            cursor.execute("SELECT id, username, email FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user:
                if user['email'] != new_email:
                    # Update email
                    cursor.execute(
                        "UPDATE users SET email = %s WHERE username = %s",
                        (new_email, username)
                    )
                    print(f"✅ Updated {username}: {user['email']} → {new_email}")
                else:
                    print(f"✅ {username} already has correct email: {new_email}")
            else:
                print(f"❌ User {username} not found")
        
        # Commit changes
        conn.commit()
        
        # Verify updates
        print("\n📋 Current test user emails:")
        for username in email_updates.keys():
            cursor.execute("SELECT username, email FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user:
                print(f"   {user['username']}: {user['email']}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Email updates completed successfully!")
        
    except Exception as e:
        print(f"❌ Error updating emails: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Updating test user emails...")
    success = update_test_user_emails()
    
    if success:
        print("\n🎉 Done! Test users now have @binge.de email addresses.")
        print("The existing App Runner deployment will now return the updated emails.")
        print("\nFor invitation testing, use:")
        print("  - testuser01@binge.de (for PLAYER01)")
        print("  - testuser02@binge.de (for PLAYER02)")
    else:
        print("\n💥 Failed to update emails.") 