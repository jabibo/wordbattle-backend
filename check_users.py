#!/usr/bin/env python3
"""
Script to check which users have @binge.de email addresses
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection parameters
DB_HOST = "wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com"
DB_NAME = "wordbattle"
DB_USER = "postgres"
DB_PASSWORD = "Wordbattle2024"
DB_PORT = "5432"

def check_users():
    """Check users with @binge.de emails"""
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
        
        # Check for @binge.de emails
        cursor.execute("SELECT id, username, email FROM users WHERE email LIKE '%@binge.de'")
        binge_users = cursor.fetchall()
        
        print("📧 Users with @binge.de emails:")
        for user in binge_users:
            print(f"   ID: {user['id']}, Username: {user['username']}, Email: {user['email']}")
        
        # Check the specific users we want to update
        target_users = ["testuser_80cb46b1", "testuser_48a04d07_1"]
        print(f"\n🎯 Target users for email update:")
        for username in target_users:
            cursor.execute("SELECT id, username, email FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user:
                print(f"   ID: {user['id']}, Username: {user['username']}, Email: {user['email']}")
            else:
                print(f"   ❌ User {username} not found")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking users: {e}")

if __name__ == "__main__":
    check_users() 