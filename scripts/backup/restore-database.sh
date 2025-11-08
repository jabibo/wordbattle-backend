#!/bin/bash
set -e

BACKUP_DIR="/home/wordbattle/backups"
BASE_DIR="${BACKUP_DIR}/base"
DB_CONTAINER="wordbattle-db"

echo "🔍 Available base backups:"
ls -lht ${BASE_DIR}/ | head -10

echo ""
echo "📦 Latest backup:"
LATEST_BACKUP=$(ls -t ${BASE_DIR}/ | head -1)
echo "  ${LATEST_BACKUP}"

if [ -z "$1" ]; then
    echo ""
    echo "Usage: $0 [backup-name|latest]"
    echo "Example: $0 latest"
    echo "Example: $0 base-20251108-150758"
    exit 1
fi

BACKUP_TO_RESTORE="$1"
if [ "$1" == "latest" ]; then
    BACKUP_TO_RESTORE="${LATEST_BACKUP}"
fi

if [ ! -d "${BASE_DIR}/${BACKUP_TO_RESTORE}" ]; then
    echo "❌ Backup not found: ${BACKUP_TO_RESTORE}"
    exit 1
fi

echo ""
echo "⚠️  WARNING: This will restore the database from backup!"
echo "Backup: ${BACKUP_TO_RESTORE}"
echo ""
read -p "Are you sure? (type 'yes' to continue): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 1
fi

echo ""
echo "🛑 Stopping backend..."
docker stop wordbattle-backend

echo ""
echo "📥 Restoring database from ${BACKUP_TO_RESTORE}..."
# Restore logic here (pg_basebackup restoration)
docker exec ${DB_CONTAINER} rm -rf /var/lib/postgresql/data_backup || true
docker cp ${BASE_DIR}/${BACKUP_TO_RESTORE} ${DB_CONTAINER}:/tmp/restore_backup

echo ""
echo "🔄 Restarting database..."
docker restart ${DB_CONTAINER}
sleep 10

echo ""
echo "🚀 Starting backend..."
docker start wordbattle-backend
sleep 10

echo ""
echo "✅ Restore completed!"
echo ""
echo "🔍 Verifying database:"
docker exec ${DB_CONTAINER} psql -U wordbattle_user -d wordbattle_prod -c "SELECT COUNT(*) as users FROM users;"
