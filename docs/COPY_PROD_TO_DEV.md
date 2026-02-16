# Copy Production Database to Development

**Purpose**: Refresh local dev database with production data for realistic testing.

---

## Prerequisites

- SSH access to wordbattle2.de (`ssh wordbattle2.de` works)
- Dev Docker running: `docker compose -f docker-compose.dev.yml up -d`

---

## Quick Run

```bash
cd /Users/janbinge/git/wordbattle/wordbattle-backend
./scripts/copy_prod_to_dev.sh
```

---

## What It Does

1. **Dumps** production DB (`wordbattle_prod`) from wordbattle2.de
2. **Copies** dump to local `backups/wordbattle-prod-YYYYMMDD-HHMMSS.dump`
3. **Stops** dev backend (releases DB connections)
4. **Resets** dev database (drop + recreate `wordbattle`)
5. **Restores** dump into dev
6. **Starts** dev backend

---

## Database Mapping

| | Production | Development |
|---|------------|-------------|
| Container | wordbattle-db | wordbattle-db-dev |
| Database | wordbattle_prod | wordbattle |
| User | wordbattle_user | postgres |

---

## Troubleshooting

### "connection refused" (SSH)
- Ensure SSH works: `ssh wordbattle2.de`
- Check ~/.ssh/config has ServerAliveInterval

### "container not found"
- Prod: Ensure wordbattle-db is running on server
- Dev: Run `docker compose -f docker-compose.dev.yml up -d`

### pg_restore errors
- Some "already exists" warnings are normal (extensions, etc.)
- If restore fails completely, check dump file exists in backups/

### Port 5432 conflict
- Dev postgres uses 5432. Stop any local postgres: `brew services stop postgresql` (if applicable)
