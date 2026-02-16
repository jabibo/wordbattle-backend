# Unhealthy Backend Container - Root Cause & Fix

**Date**: February 6, 2026  
**Server**: wordbattle2.de  
**Symptom**: `wordbattle-backend` container shows status "unhealthy"

---

## Root Cause

The Docker health check is configured to use **`wget`**, but **`wget` is not installed** in the slim Python container image.

### Health Check Configuration (Current - Broken)

```json
{
  "Test": ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8000/health"],
  "Interval": 30s,
  "Timeout": 10s,
  "StartPeriod": 40s,
  "Retries": 3
}
```

### Error Message

```
exec: "wget": executable file not found in $PATH
```

Every health check attempt fails because `wget` does not exist in the container.

---

## Important: Backend Is Actually Healthy

The backend application **is working correctly**:

- **Health endpoint**: `curl http://localhost:8000/health` returns:
  ```json
  {"status":"healthy","database":"healthy","computer_player":"not_ready","environment":"production"}
  ```
- **Database**: Connected and healthy
- **API**: Responding to requests

The "unhealthy" status is **only** a Docker health check configuration bug, not an application problem.

---

## Fix Options

### Option 1: Add HEALTHCHECK to Dockerfile (Recommended for Future Builds)

Add a proper health check using `curl` (which is already installed in the image) to `Dockerfile.cloudrun`:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

Then rebuild and redeploy the container.

### Option 2: Recreate Container with Correct Health Check (Immediate Fix)

Without rebuilding the image, recreate the container with an explicit health check using `curl`.

**Run on server** (e.g. `ssh -i ~/.ssh/id_rsa_strato_server root@wordbattle2.de`):

```bash
# Stop and remove current container
docker stop wordbattle-backend
docker rm wordbattle-backend

# Start with correct health check (curl instead of wget)
docker run -d \
  --name wordbattle-backend \
  --network wordbattle_wordbattle-net \
  --restart always \
  -p 127.0.0.1:8000:8000 \
  --env-file /home/wordbattle/wordbattle/app/deploy.env \
  --health-cmd='curl -f http://localhost:8000/health || exit 1' \
  --health-interval=30s \
  --health-timeout=10s \
  --health-start-period=40s \
  --health-retries=3 \
  -v /home/wordbattle/wordbattle/logs/app:/app/logs \
  wordbattle-backend:latest \
  sh -c 'uvicorn app.main:app --host 0.0.0.0 --port 8000'

# Wait ~45 seconds, then verify
sleep 45
docker ps --filter name=wordbattle-backend
# Should show: Up X seconds (healthy)
```

### Option 3: Disable Health Check (Not Recommended)

If you don't need health monitoring:

```bash
docker run -d \
  --name wordbattle-backend \
  --no-healthcheck \
  ...
```

---

## Verification

After applying the fix:

```bash
# Wait ~40 seconds for start period, then check status
docker ps

# Should show: Up X seconds (healthy)
# Instead of: Up X days (unhealthy)

# Verify health endpoint
curl -s http://127.0.0.1:8000/health | jq
```

---

## Summary

| Item | Status |
|------|--------|
| **Root cause** | Health check uses `wget` (not installed) |
| **Backend app** | ✅ Working correctly |
| **Database** | ✅ Healthy |
| **Fix** | Use `curl` instead of `wget` in health check |
| **Downtime** | ~10 seconds (container restart) |
