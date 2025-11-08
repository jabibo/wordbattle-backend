# Migrating Production Data from Google Cloud SQL to the Self-Hosted Server

> **Goal:** Replace the Google Cloud SQL production database with the self-hosted PostgreSQL instance that powers `https://wordbattle2.de`, transferring all existing production data safely.

---

## 1. Prerequisites

- **Approvals & Downtime**
  - Explicit go-ahead for production downtime.
  - Users informed about the maintenance window.
  - Rollback owner identified.
- **Access**
  - `gcloud` CLI configured with access to the `wordbattle-secure` project.
  - Ability to run the Cloud SQL Auth proxy or `pg_dump` directly against Cloud SQL.
  - SSH access to the self-hosted server (`wordbattle2.de`) with sudo or docker privileges.
  - Permissions on the self-hosted PostgreSQL container (`wordbattle-db`) and backend container.
- **Local Dependencies**
  - `pg_dump`, `psql`, and `gcloud` installed on the machine orchestrating the migration.
  - Sufficient local disk space for database dumps (current production DB ≈ few GB; verify before proceeding).

---

## 2. Migration Overview

| Step | Summary | Expected Downtime |
| ---- | ------- | ---------------- |
| 1 | Freeze production writes | 5 minutes |
| 2 | Export Cloud SQL data | 5–10 minutes (depends on DB size) |
| 3 | Copy dump to self-hosted server | 5 minutes |
| 4 | Stop self-hosted backend, back up current DB | 5 minutes |
| 5 | Import production dump | 10–20 minutes |
| 6 | Smoke tests & verification | 10 minutes |
| 7 | Re-enable traffic | — |

Total estimated downtime: **~45 minutes** (plan conservatively for 60).

---

## 3. Detailed Procedure

### Step 0 – Pre-Migration Checklist

1. Announce downtime to stakeholders and users.
2. Pause all WordBattle deployments (frontend & backend).
3. Confirm no schema migrations are pending.
4. Verify you have a recent Cloud SQL snapshot; if not, trigger one:
   ```bash
   gcloud sql backups create --instance=wordbattle-db
   ```
5. Confirm self-hosted server has enough free disk space:
   ```bash
   ssh wordbattle2.de "df -h /"
   ```

### Step 1 – Freeze Writes in Production

1. Enable maintenance mode in the frontend (or temporarily disable the login/registration endpoints) to prevent new writes.
2. Optionally, stop the Cloud Run backend to guarantee write silence:
   ```bash
   gcloud run services update wordbattle-backend-prod \
     --platform managed \
     --project wordbattle-secure \
     --region europe-west1 \
     --set-env-vars MAINTENANCE_MODE=true
   ```
3. Wait a few minutes to ensure all in-flight transactions complete.

### Step 2 – Export Data from Cloud SQL

#### Option A: Direct `pg_dump` via Cloud SQL Auth Proxy (preferred)

```bash
# Start Cloud SQL proxy in another terminal
cloud_sql_proxy --instances=wordbattle-secure:europe-west1:wordbattle-db=tcp:5433

# Run pg_dump
PGPASSWORD="<PROD_DB_PASSWORD_FROM_SECRET>" pg_dump \
  -h 127.0.0.1 -p 5433 \
  -U wordbattle \
  -d wordbattle_prod \
  --format=custom \
  --no-owner \
  --file=wordbattle-prod-$(date +%Y%m%d-%H%M).dump
```

#### Option B: `gcloud sql export`

```bash
EXPORT_URI="gs://wordbattle-backups/wordbattle-prod-$(date +%Y%m%d-%H%M).sql.gz"
gcloud sql export sql wordbattle-db "$EXPORT_URI" \
  --database=wordbattle_prod \
  --project=wordbattle-secure
gsutil cp "$EXPORT_URI" .
```

> **Note:** The export can take several minutes. Verify the dump integrity before proceeding.

### Step 3 – Transfer Dump to Self-Hosted Server

```bash
scp wordbattle-prod-*.dump root@wordbattle2.de:/root/backups/
```

Keep the file in `/root/backups/` (a directory outside the Docker bind mounts) to avoid accidental exposure.

### Step 4 – Prepare the Self-Hosted Server

1. SSH into the server:
   ```bash
   ssh root@wordbattle2.de
   cd /home/wordbattle/wordbattle/app
   ```
2. Stop backend containers to prevent writes during import:
   ```bash
   docker stop wordbattle-backend
   ```
3. Back up current self-hosted DB (in case rollback is needed):
   ```bash
   docker exec wordbattle-db pg_dump \
     -U wordbattle_user \
     -d wordbattle_prod \
     --format=custom \
     --file=/var/lib/postgresql/data/backup-pre-migration.dump
   ```
4. Optionally, copy the backup off the server for safekeeping.

### Step 5 – Restore Cloud SQL Dump into Self-Hosted DB

1. Drop and recreate the database to ensure a clean slate:
   ```bash
   docker exec -it wordbattle-db psql -U postgres <<'SQL'
   REVOKE CONNECT ON DATABASE wordbattle_prod FROM public;
   SELECT pid, pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE datname = 'wordbattle_prod' AND pid <> pg_backend_pid();
   DROP DATABASE wordbattle_prod;
   CREATE DATABASE wordbattle_prod OWNER wordbattle_user;
   GRANT ALL PRIVILEGES ON DATABASE wordbattle_prod TO wordbattle_user;
   SQL
   ```
2. Restore the production dump:
   ```bash
  docker exec -i wordbattle-db pg_restore \
     -U wordbattle_user \
     -d wordbattle_prod \
     --clean \
     --if-exists \
     /var/lib/postgresql/data/backups/wordbattle-prod-<timestamp>.dump
   ```
   *(Adjust path if you stored the dump elsewhere.)*

3. Ensure required extensions exist (the import should recreate them, but double-check):
   ```bash
   docker exec -it wordbattle-db psql -U wordbattle_user -d wordbattle_prod \
     -c "CREATE EXTENSION IF NOT EXISTS citext;"
   ```

### Step 6 – Restart Backend and Run Migrations

```bash
docker run -d --name wordbattle-backend \
  --network wordbattle_wordbattle-net \
  --restart always \
  -p 8000:8000 \
  --env-file /home/wordbattle/wordbattle/app/deploy.env \
  9a0f0279f061 \
  sh -c 'uvicorn app.main:app --host 0.0.0.0 --port 8000'
```

If Alembic migrations are needed, run them now (they should be part of application startup; confirm logs).

### Step 7 – Post-Migration Verification

1. Confirm health endpoint:
   ```bash
   curl -s https://wordbattle2.de/health | jq
   ```
   Expect `{"status":"healthy","database":"healthy","computer_player":"ready",...}`.
2. Run smoke tests:
   - User login & registration (if allowed during maintenance).
   - Create a game, make a move.
   - Ensure WebSocket play works.
3. Verify administrative dashboards and RabbitMQ/Redis integrations if applicable.
4. Update frontend clients to point to the self-hosted backend as production (if not already done).

### Step 8 – Resume Traffic & Monitoring

1. Disable maintenance mode on the frontend or re-enable Cloud Run (if it was disabled for maintenance).
2. Monitor logs and key metrics for at least 30–60 minutes.
3. Remove local dump copies or move them to encrypted storage.

---

## 4. Rollback Plan

If critical issues appear:

1. Re-enable Cloud Run backend pointing to Cloud SQL.
2. Restore the self-hosted DB from the `backup-pre-migration.dump` snapshot.
3. Revert frontend environment configuration to Cloud Run URLs.
4. Communicate rollback and the reason to stakeholders.

---

## 5. Additional Notes

- **Security:** The dump contains sensitive PII. Handle it according to company security policy and delete copies ASAP.
- **Testing**: If possible, rehearse the procedure using the dev database before touching production.
- **Documentation:** Update environment documents and runbooks after migration to reflect the new production topology.
- **Existing Docs:** See `docs/troubleshooting/SELF_HOSTED_DATABASE_RECOVERY.md` for recovering the self-hosted DB if issues arise post-migration.

---

By following this checklist, you can confidently migrate production data from Cloud SQL to the self-hosted WordBattle infrastructure with a controlled downtime window and a clear rollback path.

