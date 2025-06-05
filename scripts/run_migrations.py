#!/usr/bin/env python3
"""
Simple script to run database migrations manually.
Useful for testing and local development.
"""
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database_manager import run_migrations

if __name__ == "__main__":
    print("🚀 Running database migrations...")
    result = run_migrations()
    
    if result["success"]:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ Migration failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)
    
    print("🎉 Migration script completed!") 