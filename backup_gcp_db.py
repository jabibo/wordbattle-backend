#!/usr/bin/env python3
import os
import subprocess
import sys
from datetime import datetime

# GCP Connection details
CONNECTION_NAME = "wordbattle-secure:europe-west1:wordbattle-db"
DB_NAME = "wordbattle_prod"
DB_USER = "wordbattle"
DB_PASSWORD = "HKrzBR4nMpF4ddgf"

# Create backup filename
backup_file = f"wordbattle-prod-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.sql"

print(f"🔄 Starting database backup...")
print(f"📁 Backup file: {backup_file}")

# Start Cloud SQL Proxy
print("🔌 Starting Cloud SQL Proxy...")
proxy_cmd = f"./cloud_sql_proxy -instances={CONNECTION_NAME}=tcp:5433"
proxy_process = subprocess.Popen(proxy_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Wait for proxy to start
import time
time.sleep(5)

# Run pg_dump
print("📤 Dumping database...")
env = os.environ.copy()
env['PGPASSWORD'] = DB_PASSWORD

dump_cmd = [
    'pg_dump',
    '-h', '127.0.0.1',
    '-p', '5433',
    '-U', DB_USER,
    '-d', DB_NAME,
    '-F', 'p',
    '-f', backup_file
]

try:
    result = subprocess.run(dump_cmd, env=env, capture_output=True, text=True, timeout=300)
    
    if result.returncode == 0:
        size = os.path.getsize(backup_file) / (1024 * 1024)
        print(f"✅ Backup created successfully: {backup_file} ({size:.2f} MB)")
    else:
        print(f"❌ Backup failed: {result.stderr}")
        sys.exit(1)
finally:
    # Kill proxy
    proxy_process.terminate()
    print("🔌 Cloud SQL Proxy stopped")

print(f"\n✅ Backup complete: {backup_file}")
