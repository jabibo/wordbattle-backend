#!/usr/bin/env python3
"""
Script to check what tables exist in the database
"""
import os
from sqlalchemy import create_engine, text
from app.config import DATABASE_URL

def check_tables():
    """Check what tables exist in the database"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all table names
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result]
        
        print("📋 Tables in database:")
        for table in tables:
            print(f"  ✅ {table}")
        
        # Check specifically for game_invitations
        if "game_invitations" in tables:
            print(f"\n🎯 game_invitations table EXISTS")
            
            # Check the structure
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'game_invitations'
                ORDER BY ordinal_position;
            """))
            
            print("   Columns:")
            for row in result:
                print(f"     - {row[0]} ({row[1]}) {'NULL' if row[2] == 'YES' else 'NOT NULL'}")
                
        else:
            print(f"\n❌ game_invitations table DOES NOT EXIST")

if __name__ == "__main__":
    check_tables() 