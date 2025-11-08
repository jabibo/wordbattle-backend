# WordBattle Database Backup System

## Overview
Automated incremental backup system using PostgreSQL WAL archiving.

## Backup Schedule
- **Incremental backups**: Every 15 minutes (WAL files)
- **Full base backup**: Once daily at 2 AM
- **Retention**: 7 days for base backups, 3 days for WAL files

## Backup Locations
- Base backups: `/home/wordbattle/backups/base/`
- WAL archive: `/home/wordbattle/backups/wal_archive/`
- Log file: `/var/log/wordbattle-backup.log`

## Manual Backup
```bash
# Force a base backup now
/home/wordbattle/scripts/backup-incremental.sh base

# Check backup status
ls -lh /home/wordbattle/backups/base/
tail -f /var/log/wordbattle-backup.log
```

## Restore Database
```bash
# List available backups
ls -lht /home/wordbattle/backups/base/

# Restore from latest backup
/home/wordbattle/scripts/restore-database.sh latest

# Restore from specific backup
/home/wordbattle/scripts/restore-database.sh base-20251108-150758
```

## Backup Efficiency
- **Base backup size**: ~48 MB (compressed)
- **WAL files**: Very small (KB to MB per 15 min)
- **Total disk usage**: ~500 MB for 7 days of backups

## Point-in-Time Recovery
With WAL archiving, you can restore to any point in the last 3 days:
1. Choose a base backup
2. Replay WAL files up to desired point in time
3. Contact admin for detailed PITR instructions

## Monitoring
```bash
# Check last backup
tail /var/log/wordbattle-backup.log

# Check backup sizes
du -sh /home/wordbattle/backups/*

# Verify cron job
crontab -l | grep backup
```
