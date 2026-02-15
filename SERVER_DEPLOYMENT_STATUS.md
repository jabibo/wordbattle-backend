# WordBattle Backend - Production Server Deployment Status

**Date**: February 6, 2026  
**Server**: wordbattle2.de (Self-Hosted)  
**Analysis**: Complete server setup determination

---

## ✅ CONFIRMED: Docker-Based Deployment (WITHOUT docker-compose)

### **Production Server Setup on wordbattle2.de:**

```
┌─────────────────────────────────────────────────┐
│ PRODUCTION SERVER: wordbattle2.de              │
├─────────────────────────────────────────────────┤
│ ✅ Docker Containers (4 running)               │
│   ├── wordbattle-backend (Up 3 days, unhealthy)│
│   ├── wordbattle-db (PostgreSQL, healthy)      │
│   ├── wordbattle-redis (healthy)               │
│   └── wordbattle-nginx (healthy)               │
│                                                 │
│ ✅ Network: wordbattle_wordbattle-net          │
│ ✅ Backend Port: 127.0.0.1:8000->8000          │
│ ✅ HTTPS: Nginx reverse proxy (443->8000)     │
│ ✅ Database: Internal Docker network           │
│                                                 │
│ ❌ NO systemd services                         │
│ ❌ NO docker-compose.yml in use                │
│                                                 │
│ 🐳 Deployment Method: Direct Docker run        │
└─────────────────────────────────────────────────┘
```

---

## 🔍 Current Deployment Details

### **Backend Container:**

- **Image**: `wordbattle-backend:latest`
- **Image ID**: `sha256:48fd450dd338...`
- **Created**: November 8, 2025, 12:57:15 UTC
- **Status**: Up 3 days (unhealthy) ⚠️
- **Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Network**: `wordbattle_wordbattle-net`
- **Ports**: `127.0.0.1:8000->8000/tcp`
- **Volume**: `/home/wordbattle/wordbattle/logs/app -> /app/logs`

### **Environment Variables (Key):**

```bash
DB_HOST=postgres  # Points to PostgreSQL container
CLOUD_PROVIDER=self-hosted
```

### **Backend Dockerfile:**

- Located: `/app/Dockerfile.cloudrun`
- Used for building the image

---

## 📦 Current Python Dependencies (In Running Container)

```python
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.4.2
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
python-jose==3.3.0
passlib==1.7.4
python-multipart==0.0.6
python-dotenv==1.0.0
pg8000==1.30.3
asyncpg==0.29.0

# AWS Dependencies
boto3==1.29.3
botocore==1.32.3

# GCP Dependencies
google-cloud-storage==2.13.0
google-cloud-secret-manager==2.16.4
google-cloud-run==0.10.0

# Common
requests==2.31.0
aiohttp==3.9.0
python-json-logger==2.0.7
structlog==23.2.0

cloud-sql-python-connector[asyncpg]==1.5.0
```

**🚨 IMPORTANT**: `firebase-admin` is **NOT installed** in the current running container!

---

## 🔧 Deployment Method Determined

### **Direct Docker Run** (NOT docker-compose)

Based on evidence:
1. ✅ Container started with `docker run` command (as seen in `SELF_HOSTED_DATABASE_RECOVERY.md`)
2. ✅ No active `docker-compose.yml` in `/home/wordbattle/wordbattle/app/`
3. ✅ Manual Docker commands used for restarts
4. ✅ Custom network: `wordbattle_wordbattle-net`

### **Last Known Docker Run Command:**

```bash
docker run -d \
  --name wordbattle-backend \
  --network wordbattle_wordbattle-net \
  --restart always \
  -p 8000:8000 \
  --env-file /home/wordbattle/wordbattle/app/deploy.env \
  9a0f0279f061 \
  sh -c 'uvicorn app.main:app --host 0.0.0.0 --port 8000'
```

*(Image ID `9a0f0279f061` is old; current is `48fd450dd338`)*

---

## 📋 Installation Strategy for Firebase Admin SDK

### **Step-by-Step Process:**

Since the server uses **direct Docker deployment**, you need to:

1. ✅ **Update `requirements.txt`** (DONE - already committed)
   ```python
   firebase-admin==6.3.0
   ```

2. ✅ **Rebuild Docker Image on Server**
   ```bash
   # On wordbattle2.de server:
   ssh -i ~/.ssh/id_rsa_strato_server root@wordbattle2.de
   
   cd /home/wordbattle/wordbattle/app
   
   # Pull latest code with updated requirements.txt
   git pull
   
   # Rebuild Docker image with new dependencies
   docker build -f Dockerfile.cloudrun -t wordbattle-backend:latest .
   ```

3. ✅ **Upload Firebase Credentials**
   ```bash
   # From your local machine:
   scp -i ~/.ssh/id_rsa_strato_server \
     wordbattle-firebase-adminsdk.json \
     root@wordbattle2.de:/home/wordbattle/wordbattle/config/
   
   # On server, secure the file:
   ssh -i ~/.ssh/id_rsa_strato_server root@wordbattle2.de
   chmod 600 /home/wordbattle/wordbattle/config/wordbattle-firebase-adminsdk.json
   ```

4. ✅ **Update Environment File**
   ```bash
   # On server:
   nano /home/wordbattle/wordbattle/app/deploy.env
   
   # Add these lines:
   FIREBASE_CREDENTIALS_PATH=/app/config/firebase-credentials.json
   ENABLE_PUSH_NOTIFICATIONS=true
   ```

5. ✅ **Stop and Remove Old Container**
   ```bash
   docker stop wordbattle-backend
   docker rm wordbattle-backend
   ```

6. ✅ **Start New Container with Updated Image and Credentials**
   ```bash
   docker run -d \
     --name wordbattle-backend \
     --network wordbattle_wordbattle-net \
     --restart always \
     -p 127.0.0.1:8000:8000 \
     --env-file /home/wordbattle/wordbattle/app/deploy.env \
     -v /home/wordbattle/wordbattle/config/wordbattle-firebase-adminsdk.json:/app/config/firebase-credentials.json:ro \
     -v /home/wordbattle/wordbattle/logs/app:/app/logs \
     wordbattle-backend:latest \
     sh -c 'uvicorn app.main:app --host 0.0.0.0 --port 8000'
   ```

7. ✅ **Verify Installation**
   ```bash
   # Check if container is running
   docker ps | grep wordbattle-backend
   
   # Check logs for Firebase initialization
   docker logs wordbattle-backend -f
   # Look for: "Firebase Admin initialized"
   
   # Verify Firebase package is installed
   docker exec wordbattle-backend pip list | grep firebase
   # Expected: firebase-admin  6.3.0
   
   # Test backend health
   curl -s https://wordbattle2.de/health | jq
   ```

---

## ⚠️ Current Issues to Fix

### **Backend Container Status: Unhealthy**

The backend has been running for 3 days but is marked as **unhealthy**.

**Possible Causes:**
1. Database connection issues (`DB_HOST=postgres` might be wrong)
2. Health check endpoint failing
3. Missing dependencies
4. Configuration mismatch

**Recommended Action:**
```bash
# Check health endpoint
curl -s http://localhost:8000/health

# Check database connectivity
docker exec wordbattle-backend python3 -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database OK')
"
```

---

## 🎯 Complete Installation Checklist for Push Notifications

### **Prerequisites:**
- [x] Firebase project created
- [x] Firebase credentials JSON downloaded
- [x] `requirements.txt` updated (committed to Git)
- [x] Server SSH access configured (`~/.ssh/id_rsa_strato_server`)

### **On Production Server (wordbattle2.de):**

**Time Estimate: 15-20 minutes**

- [ ] Pull latest code with updated `requirements.txt`
- [ ] Rebuild Docker image (includes `firebase-admin==6.3.0`)
- [ ] Upload Firebase credentials JSON
- [ ] Update `deploy.env` with Firebase variables
- [ ] Stop old container
- [ ] Start new container with:
  - Updated image
  - Firebase credentials volume mount
  - Updated environment variables
- [ ] Verify Firebase SDK installed
- [ ] Run database migration (Alembic) for 3 new tables
- [ ] Test push notification endpoint
- [ ] Monitor logs for errors

---

## 🔐 Security Notes

1. **SSH Access**: Using private key `~/.ssh/id_rsa_strato_server`
2. **Firebase Credentials**: Must be mounted read-only (`:ro`)
3. **File Permissions**: `chmod 600` on credentials file
4. **Environment File**: Already contains sensitive credentials
5. **Git Ignore**: Firebase credentials already excluded

---

## 📊 Container Resource Usage

```bash
# Check resource usage on server
docker stats wordbattle-backend --no-stream

# Current setup:
# - No resource limits set
# - Shared host network
# - Internal Docker network for database
```

---

## 🚀 Deployment History

- **Last Deployed**: November 8, 2025, 12:57:15 UTC (3 days ago)
- **Deployment Method**: Manual Docker build + run
- **Migration**: Migrated from Google Cloud Run to self-hosted (Nov 2025)
- **Database**: Migrated from Cloud SQL to self-hosted PostgreSQL

---

## 📚 Related Documentation

- **`PUSH_NOTIFICATIONS_SELF_HOSTED_SETUP.md`** - Complete Firebase setup guide
- **`QUICK_SETUP_PUSH_NOTIFICATIONS.md`** - 5-minute quick reference
- **`docs/troubleshooting/SELF_HOSTED_DATABASE_RECOVERY.md`** - Database recovery
- **`docs/MIGRATION_GCP_TO_SELF_HOSTED.md`** - GCP to self-hosted migration

---

## 🎯 Next Steps

1. **Immediate**: Fix backend health status (currently unhealthy)
2. **Then**: Proceed with Firebase Admin SDK installation
3. **After**: Implement push notification backend logic
4. **Finally**: Deploy and test with iOS app

---

## 📝 Summary

**Your production server uses:**
- ✅ **Docker** (direct `docker run`, NOT docker-compose)
- ✅ **4 containers**: backend, database, redis, nginx
- ✅ **Self-hosted**: No Cloud Run, no managed services
- ✅ **Network**: Custom Docker network
- ✅ **Deployment**: Manual Docker commands
- ❌ **No systemd services**
- ❌ **No docker-compose.yml active**

**To install Firebase Admin SDK:**
1. Rebuild Docker image with updated `requirements.txt`
2. Mount Firebase credentials as volume
3. Restart container with new image

**Estimated time**: 15-20 minutes (including verification)

---

**Status**: Ready to proceed with Firebase installation ✅  
**Risk Level**: Low (just adding a Python package and credentials)  
**Downtime**: ~2 minutes (container restart only)
