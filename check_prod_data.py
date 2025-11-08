#!/usr/bin/env python3
import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="35.240.110.171",
        port=5432,
        database="wordbattle_prod",
        user="wordbattle",
        password="HKrzBR4nMpF4ddgf",
        connect_timeout=10
    )
    
    cursor = conn.cursor()
    
    # Check counts
    tables = ['users', 'games', 'moves', 'wordlists', 'game_invitations']
    
    print("📊 Production Database Contents:")
    print("=" * 50)
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:20s}: {count:>10,} records")
    
    print("=" * 50)
    
    cursor.close()
    conn.close()
    print("\n✅ Connection successful")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Trying alternative approach: just re-initialize wordlists on new server")
    sys.exit(1)
