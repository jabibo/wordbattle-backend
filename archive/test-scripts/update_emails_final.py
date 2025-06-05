#!/usr/bin/env python3
"""
Direct database update script to change test user emails to @binge.de format.
This provides an immediate solution while App Runner deployment issues are resolved.
"""

import psycopg2
import sys

# Database connection parameters
DB_CONFIG = {
    'host': 'wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com',
    'database': 'wordbattle',
    'user': 'postgres',
    'password': 'Wordbattle2024',
    'port': 5432
}

def update_user_emails():
    """Update test user emails to @binge.de format"""
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Email updates mapping
        email_updates = [
            ('player01', 'player01@binge.de'),
            ('player02', 'player02@binge.de')
        ]
        
        print("\nUpdating user emails...")
        
        for username, new_email in email_updates:
            # Check if user exists
            cursor.execute("SELECT id, username, email FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user:
                user_id, current_username, current_email = user
                print(f"Found user: {current_username} (ID: {user_id}) - Current email: {current_email}")
                
                if current_email != new_email:
                    # Update email
                    cursor.execute("UPDATE users SET email = %s WHERE username = %s", (new_email, username))
                    print(f"✅ Updated {username} email: {current_email} → {new_email}")
                else:
                    print(f"✅ {username} email already correct: {current_email}")
            else:
                print(f"❌ User '{username}' not found in database")
        
        # Commit changes
        conn.commit()
        print("\n✅ All email updates committed successfully!")
        
        # Verify updates
        print("\nVerifying updates...")
        for username, expected_email in email_updates:
            cursor.execute("SELECT username, email FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user:
                current_username, current_email = user
                status = "✅" if current_email == expected_email else "❌"
                print(f"{status} {current_username}: {current_email}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Email update completed successfully!")
        print("\nYou can now test the updated emails at:")
        print("https://nmexamntve.eu-central-1.awsapprunner.com/debug/tokens")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating emails: {e}")
        return False

if __name__ == "__main__":
    print("WordBattle Email Update Script")
    print("=" * 40)
    
    success = update_user_emails()
    
    if success:
        print("\n✅ Script completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Script failed!")
        sys.exit(1) 