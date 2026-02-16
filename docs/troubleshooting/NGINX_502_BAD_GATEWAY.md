# Nginx 502 Bad Gateway - Debugging & Fix

**Date**: February 15, 2026  
**Server**: wordbattle2.de  
**Symptom**: `https://wordbattle2.de/health` returns 502 Bad Gateway

---

## Investigation Summary

### What Was Checked

1. **Nginx config** (`/home/wordbattle/wordbattle/nginx/conf.d/`)
   - Upstream: `backend:8000` ✅
   - `/health` location: proxies to `http://backend` ✅
   - Config is correct

2. **Docker networks**
   - Nginx and backend both on `wordbattle_wordbattle-net` ✅
   - Nginx can resolve `backend` hostname ✅

3. **Backend reachability from nginx**
   ```bash
   docker exec wordbattle-nginx curl -s http://backend:8000/health
   ```
   **Result**: Returns healthy JSON ✅
   ```json
   {"status":"healthy","database":"healthy","computer_player":"not_ready","environment":"production"}
   ```

### Root Cause

When the **backend container is recreated** (e.g. after `docker compose up -d backend`), nginx may hold **stale connections** in its upstream keepalive pool. Those connections point to the old (stopped) backend container. New requests get 502 because nginx tries to reuse dead connections.

---

## Fix

**Restart nginx** to reset the upstream connection pool:

```bash
ssh wordbattle2.de
docker restart wordbattle-nginx
```

Or from the server directly:

```bash
cd /home/wordbattle/wordbattle
docker restart wordbattle-nginx
```

**Downtime**: ~2–3 seconds

---

## Verification

```bash
# After restart, wait a few seconds
sleep 5
curl -s https://wordbattle2.de/health
# Expected: {"status":"healthy",...}
```

---

## Prevention: Restart Nginx When Backend Changes

When updating or recreating the backend, restart nginx in the same step:

```bash
cd /home/wordbattle/wordbattle
docker compose -f docker-compose.production.yml up -d backend
docker restart wordbattle-nginx
```

Or add to your deployment script.

---

## Nginx Config Reference

- **Upstream**: `backend:8000` (Docker DNS resolves `backend` to the backend container)
- **Health endpoint**: `/health` → proxied to backend, no rate limiting
- **Main app**: `/` → proxied to backend
- **API**: `/api/` → proxied to backend
- **WebSocket**: `/ws/` → proxied to backend
