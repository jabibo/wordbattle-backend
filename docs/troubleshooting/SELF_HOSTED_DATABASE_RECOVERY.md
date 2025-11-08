# Self-Hosted Database Recovery (November 2025)

This document captures the adjustments applied on 2025-11-04 to restore the self-hosted WordBattle backend at `https://wordbattle2.de`. The backend pods were healthy, but the `/health` endpoint reported `database: unhealthy` because the application attempted to connect to Google Cloud SQL instead of the local PostgreSQL container.

## Symptoms

- `/health` returned `{"status":"unhealthy","database":"unhealthy"}`.
- Backend logs showed `google.auth.exceptions.DefaultCredentialsError` and later `password authentication failed for user "wordbattle"`.
- Docker containers were running (`wordbattle-backend`, `wordbattle-db`, `wordbattle-nginx`), but the backend container was missing the local database configuration.

## Root Causes

1. `DB_HOST` was not defined in `/home/wordbattle/wordbattle/app/deploy.env`, so the backend fell back to the Cloud SQL connector.
2. The database credentials in `deploy.env` (`DB_USER=wordbattle`, `DB_PASSWORD=...`) did not match the credentials used by the local PostgreSQL container (`wordbattle_user` / `c6976e...`).

## Fixes Applied

1. Updated the env file used by Docker-based deployments:
   ```bash
   # /home/wordbattle/wordbattle/app/deploy.env
   DB_HOST=wordbattle-db
   DB_PORT=5432
   DB_USER=wordbattle_user
   DB_PASSWORD=c6976e0feda09e8660c47965334f98df345547c38a17ded4e76969834b425be7
   ```
2. Restarted the backend container with the corrected configuration:
   ```bash
   docker stop wordbattle-backend
   docker rm wordbattle-backend
   docker run -d \
     --name wordbattle-backend \
     --network wordbattle_wordbattle-net \
     --restart always \
     -p 8000:8000 \
     --env-file /home/wordbattle/wordbattle/app/deploy.env \
     9a0f0279f061 \
     sh -c 'uvicorn app.main:app --host 0.0.0.0 --port 8000'
   ```

## Verification

- `curl https://wordbattle2.de/health` now returns `{"status":"healthy","database":"healthy"}`.
- Backend logs confirm successful connection to `postgresql+pg8000://wordbattle_user@wordbattle-db:5432/wordbattle_prod`.

## Follow-Up

- Consider storing the Docker-based self-hosted configuration in version control or Ansible to avoid drift.
- Review whether the Cloud SQL connector binaries (`cloud_sql_proxy`) are still required on the self-hosted server.
- Ensure `/home/wordbattle/wordbattle/app/deploy.env` stays synchronized with local PostgreSQL container credentials after future password rotations.

