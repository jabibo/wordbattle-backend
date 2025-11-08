#!/bin/bash
set -e

BACKUP_DIR="/home/wordbattle/backups"
WAL_DIR="${BACKUP_DIR}/wal_archive"
BASE_DIR="${BACKUP_DIR}/base"
DB_CONTAINER="wordbattle-db"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Ensure directories exist
mkdir -p ${WAL_DIR}
mkdir -p ${BASE_DIR}

# Function to do base backup (full backup, run daily)
do_base_backup() {
    echo "📦 Creating base backup at $(date)"
    BACKUP_NAME="base-${TIMESTAMP}"
    
    # Use pg_basebackup for efficient base backup
    docker exec ${DB_CONTAINER} pg_basebackup -U wordbattle_user -D /tmp/${BACKUP_NAME} -Ft -z -P
    
    # Copy from container to host
    docker cp ${DB_CONTAINER}:/tmp/${BACKUP_NAME} ${BASE_DIR}/
    
    # Cleanup old base backups (keep last 7 days)
    find ${BASE_DIR} -name "base-*" -type d -mtime +7 -exec rm -rf {} \;
    
    SIZE=$(du -sh ${BASE_DIR}/${BACKUP_NAME} | cut -f1)
    echo "✅ Base backup completed (Size: ${SIZE})"
}

# Function to archive WAL files (runs every 15 min)
do_wal_archive() {
    echo "📝 Archiving WAL files at $(date)"
    
    # Force a WAL switch to archive current segment
    docker exec ${DB_CONTAINER} psql -U wordbattle_user -d wordbattle_prod -c "SELECT pg_switch_wal();" > /dev/null
    
    # WAL files are continuously archived by PostgreSQL if configured
    WAL_COUNT=$(find ${WAL_DIR} -name "*.wal" 2>/dev/null | wc -l)
    WAL_SIZE=$(du -sh ${WAL_DIR} 2>/dev/null | cut -f1 || echo "0")
    
    echo "📊 WAL archive: ${WAL_COUNT} files, ${WAL_SIZE}"
    
    # Cleanup old WAL files (keep last 3 days for point-in-time recovery)
    find ${WAL_DIR} -name "*.wal" -type f -mtime +3 -delete
}

# Check if we need a base backup (once per day at 2 AM, or if no base exists)
HOUR=$(date +%H)
BASE_EXISTS=$(find ${BASE_DIR} -name "base-$(date +%Y%m%d)*" -type d 2>/dev/null | wc -l)

if [ "$1" == "base" ] || [ ${BASE_EXISTS} -eq 0 ] || [ "${HOUR}" == "02" ]; then
    do_base_backup
fi

# Always do WAL archiving
do_wal_archive

echo "✅ Backup completed at $(date)"
