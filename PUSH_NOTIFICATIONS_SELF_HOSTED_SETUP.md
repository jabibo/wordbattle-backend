# Self-Hosted Server Requirements for Push Notifications

**Server**: wordbattle2.de (Self-Hosted)  
**Current Stack**: Python/FastAPI Backend on Docker  
**Date**: February 6, 2026

---

## 📦 Additional Dependencies Required

### 1. Python Firebase Admin SDK

**Add to `requirements.txt`:**

```python
# Push Notifications
firebase-admin==6.3.0
```

**Why needed**: 
- Firebase Admin SDK to send push notifications from your backend
- Communicates with Firebase Cloud Messaging (FCM) service
- No need to install Firebase on your server - it's just a Python library

**Installation**:
```bash
cd /Users/janbinge/git/wordbattle/wordbattle-backend
pip install firebase-admin==6.3.0

# Or add to requirements.txt and run:
pip install -r requirements.txt
```

---

## 🔑 Firebase Service Account Credentials

### 2. Firebase Service Account JSON File

**What it is**: A credentials file that allows your backend to authenticate with Firebase services.

**How to get it**:

1. **Go to Firebase Console**: https://console.firebase.google.com
2. **Select/Create Project**: WordBattle
3. **Project Settings** → Service Accounts tab
4. **Generate New Private Key** button
5. **Download JSON file** (e.g., `wordbattle-firebase-adminsdk.json`)

**Where to store it on your server**:

```bash
# Option A: Store in secure location
/opt/wordbattle/config/firebase-credentials.json

# Option B: Store in app directory (outside git)
/app/config/firebase-credentials.json

# Make sure it's readable by app user
chmod 600 /path/to/firebase-credentials.json
chown appuser:appuser /path/to/firebase-credentials.json
```

**IMPORTANT**: 
- ⚠️ **Never commit this file to Git** - it contains secret keys
- ⚠️ Add to `.gitignore`: `*firebase*.json`
- ⚠️ Backup securely - you can't download it again

---

## ⚙️ Environment Variables

### 3. Update Backend Environment Configuration

**Add to your production `.env` file** (or Docker environment):

```bash
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=/opt/wordbattle/config/firebase-credentials.json
ENABLE_PUSH_NOTIFICATIONS=true

# Optional: Firebase project details (for reference)
FIREBASE_PROJECT_ID=wordbattle-xxxxx
```

**Update**: `deploy.production.env` or your actual `.env` file on the server.

---

## 🐳 Docker Configuration Updates

### 4. Update Dockerfile (if using Docker)

**Update `Dockerfile.cloudrun`** to include Firebase credentials:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create config directory for Firebase credentials
RUN mkdir -p /app/config

# Copy the actual word files
RUN ls -la data/ && echo "Word files available:"

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**When building Docker image, mount Firebase credentials**:

```bash
# Option A: Build with credentials included (less secure)
COPY config/firebase-credentials.json /app/config/

# Option B: Mount as volume at runtime (more secure, recommended)
docker run -v /opt/wordbattle/config/firebase-credentials.json:/app/config/firebase-credentials.json ...
```

---

## 🔒 Firewall & Network Configuration

### 5. Outbound Connections Required

Your self-hosted server needs to allow **outbound HTTPS connections** to:

**Firebase Cloud Messaging**:
- `fcm.googleapis.com` (port 443)
- `fcm-xmpp.googleapis.com` (port 5228, 5229, 5230 - optional)

**Google APIs**:
- `oauth2.googleapis.com` (port 443)
- `www.googleapis.com` (port 443)

**Firewall Rules**:
```bash
# If using iptables, ensure outbound HTTPS is allowed:
sudo iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

# If using UFW:
sudo ufw allow out 443/tcp

# Usually outbound connections are allowed by default
```

**Test connectivity**:
```bash
# Test from your server
curl -I https://fcm.googleapis.com
curl -I https://oauth2.googleapis.com

# Should return 200 or similar (not connection refused)
```

---

## 📋 Complete Installation Checklist

### On Your Self-Hosted Server (wordbattle2.de):

#### Step 1: Update Requirements
```bash
# SSH into your server
ssh user@wordbattle2.de

# Navigate to backend directory
cd /path/to/wordbattle-backend

# Add to requirements.txt
echo "firebase-admin==6.3.0" >> requirements.txt

# Install
pip install -r requirements.txt

# Or if using virtual environment
source .venv/bin/activate
pip install -r requirements.txt
```

#### Step 2: Upload Firebase Credentials
```bash
# From your local machine:
scp wordbattle-firebase-adminsdk.json user@wordbattle2.de:/opt/wordbattle/config/

# On server, secure the file:
ssh user@wordbattle2.de
chmod 600 /opt/wordbattle/config/firebase-credentials.json
chown www-data:www-data /opt/wordbattle/config/firebase-credentials.json
# (Replace www-data with your app user)
```

#### Step 3: Update Environment Variables
```bash
# On server, edit your .env or environment file
nano /path/to/.env

# Add these lines:
FIREBASE_CREDENTIALS_PATH=/opt/wordbattle/config/firebase-credentials.json
ENABLE_PUSH_NOTIFICATIONS=true
```

#### Step 4: Update Docker Configuration (if using Docker)
```bash
# If using docker-compose.yml:
services:
  backend:
    # ... existing config ...
    environment:
      - FIREBASE_CREDENTIALS_PATH=/app/config/firebase-credentials.json
      - ENABLE_PUSH_NOTIFICATIONS=true
    volumes:
      - /opt/wordbattle/config/firebase-credentials.json:/app/config/firebase-credentials.json:ro
```

#### Step 5: Restart Application
```bash
# If using systemd:
sudo systemctl restart wordbattle-backend

# If using Docker:
docker-compose restart backend

# If using direct uvicorn:
# Stop existing process and start again
pkill -f "uvicorn app.main:app"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

#### Step 6: Verify Installation
```bash
# Check Firebase Admin SDK is installed
python3 -c "import firebase_admin; print('Firebase Admin SDK:', firebase_admin.__version__)"

# Should output: Firebase Admin SDK: 6.3.0

# Check credentials file exists
ls -la /opt/wordbattle/config/firebase-credentials.json

# Check app logs for Firebase initialization
tail -f /var/log/wordbattle-backend.log  # or wherever your logs are
# Should see: "Firebase Admin initialized with credentials"
```

---

## 🚫 What You DON'T Need on Self-Hosted Server

### ✅ No Additional Services Required:

- ❌ **No Firebase hosting** - Firebase is used only for push messaging
- ❌ **No Google Cloud services** - Just the Python SDK
- ❌ **No separate notification server** - Integrated in your backend
- ❌ **No Redis/RabbitMQ** - Firebase handles message delivery
- ❌ **No additional databases** - Uses your existing PostgreSQL
- ❌ **No nginx changes** - Same reverse proxy config
- ❌ **No additional ports** - Uses existing backend port (8000)

### ✅ What Actually Happens:

1. Your backend → Firebase Cloud (via HTTPS API)
2. Firebase → Apple Push Notification Service (APNs)
3. APNs → User's iPhone

**Your server only makes outbound HTTPS calls to Firebase APIs.**

---

## 🔧 Configuration Summary

### Files to Update:

1. **`requirements.txt`** - Add `firebase-admin==6.3.0`
2. **`.env`** or production environment file - Add Firebase settings
3. **`.gitignore`** - Ensure `*firebase*.json` is ignored
4. **`Dockerfile.cloudrun`** (if using Docker) - Mount credentials

### Credentials Needed:

1. **Firebase Service Account JSON** - From Firebase Console
2. **APNs Authentication Key** (.p8 file) - Upload to Firebase Console (not server)

### Environment Variables:

```bash
FIREBASE_CREDENTIALS_PATH=/opt/wordbattle/config/firebase-credentials.json
ENABLE_PUSH_NOTIFICATIONS=true
```

---

## 📊 Resource Usage

### Minimal Impact on Your Server:

- **CPU**: Negligible (just API calls to Firebase)
- **Memory**: +~10-20MB (Firebase SDK in memory)
- **Disk**: +~5MB (Firebase SDK library)
- **Network**: Minimal outbound HTTPS traffic
- **No persistent connections** - Firebase handles all real-time aspects

---

## 🧪 Testing on Self-Hosted Server

### After Installation:

```bash
# 1. Check Firebase SDK installed
python3 -c "import firebase_admin; print('✅ Firebase Admin SDK installed')"

# 2. Test credentials file accessibility
python3 << EOF
import firebase_admin
from firebase_admin import credentials

try:
    cred = credentials.Certificate('/opt/wordbattle/config/firebase-credentials.json')
    print('✅ Firebase credentials loaded successfully')
except Exception as e:
    print(f'❌ Error loading credentials: {e}')
EOF

# 3. Check backend can initialize Firebase
curl https://wordbattle2.de/health
# Should show healthy status

# 4. Test notification endpoint (after full implementation)
curl -X POST https://wordbattle2.de/push/token \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token":"test_token","platform":"ios","app_version":"1.0.6"}'
```

---

## 🔐 Security Best Practices

### Securing Firebase Credentials:

1. **File Permissions**:
   ```bash
   chmod 600 firebase-credentials.json
   chown appuser:appuser firebase-credentials.json
   ```

2. **Firewall Rules**:
   ```bash
   # Only allow outbound to Firebase IPs (optional, advanced)
   # Most servers allow all outbound HTTPS by default
   ```

3. **Environment Variables**:
   - Never hardcode credential paths
   - Use environment variables
   - Consider secret management (HashiCorp Vault, etc.)

4. **Backup**:
   - Store credentials in secure backup location
   - Document recovery process
   - Can't re-download from Firebase

---

## 🚀 Deployment Process

### For Self-Hosted Server:

```bash
# 1. Update requirements.txt locally
cd /Users/janbinge/git/wordbattle/wordbattle-backend
echo "firebase-admin==6.3.0" >> requirements.txt
git add requirements.txt
git commit -m "Add Firebase Admin SDK for push notifications"
git push

# 2. On server - pull changes
ssh user@wordbattle2.de
cd /path/to/wordbattle-backend
git pull

# 3. Install new dependency
source .venv/bin/activate  # if using venv
pip install -r requirements.txt

# 4. Upload Firebase credentials (one-time)
# From local machine:
scp /path/to/firebase-credentials.json user@wordbattle2.de:/opt/wordbattle/config/

# 5. Update environment
nano .env  # or your env file
# Add: FIREBASE_CREDENTIALS_PATH=/opt/wordbattle/config/firebase-credentials.json
# Add: ENABLE_PUSH_NOTIFICATIONS=true

# 6. Restart backend
sudo systemctl restart wordbattle-backend
# Or: docker-compose restart backend

# 7. Verify
curl https://wordbattle2.de/health
tail -f /var/log/wordbattle.log
```

---

## 📱 Integration with Existing Infrastructure

### Your Current Setup:
```
Self-Hosted Server (wordbattle2.de)
├── Nginx (reverse proxy) ✅ No changes needed
├── PostgreSQL Database ✅ Just new tables (via migration)
├── Python FastAPI Backend ✅ Just add Firebase SDK
├── SSL/TLS Certificate ✅ No changes needed
└── Docker (optional) ✅ Minor volume mount if used
```

### Changes Required:
```
✅ Add: firebase-admin==6.3.0 to requirements.txt
✅ Add: Firebase credentials JSON file on server
✅ Add: 2 environment variables
✅ Run: Database migration (3 new tables)
❌ NO changes to: Nginx, PostgreSQL, SSL, networking
```

---

## 🔄 Migration Process

### Database Changes:

The push notification feature adds 3 tables:
- `push_tokens` - Store device tokens
- `notification_preferences` - User settings
- `notification_log` - Analytics/debugging

**Run migration on server**:
```bash
cd /path/to/wordbattle-backend
source .venv/bin/activate
alembic upgrade head
```

**Rollback if needed**:
```bash
alembic downgrade -1
```

---

## ✅ Installation Summary

### What to Install on Server:

| Component | Installation Method | Size | Time |
|-----------|-------------------|------|------|
| Firebase Admin SDK | `pip install firebase-admin==6.3.0` | ~5 MB | 30 sec |
| Firebase Credentials | Upload JSON file | ~2 KB | 1 min |
| Environment Variables | Edit .env | N/A | 1 min |
| Database Tables | `alembic upgrade head` | N/A | 10 sec |

**Total Installation Time**: ~5 minutes  
**Total Additional Space**: ~5 MB  
**Additional Memory**: ~10-20 MB at runtime

---

## 🧪 Testing on Self-Hosted Server

### Verification Steps:

```bash
# 1. SSH into server
ssh user@wordbattle2.de

# 2. Verify Firebase SDK installed
python3 -c "import firebase_admin; print('✅ Installed:', firebase_admin.__version__)"

# 3. Test credentials file
python3 << 'PYTEST'
import firebase_admin
from firebase_admin import credentials
import os

cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', '/opt/wordbattle/config/firebase-credentials.json')
try:
    cred = credentials.Certificate(cred_path)
    print(f'✅ Credentials file valid: {cred_path}')
    print(f'   Project ID: {cred.project_id}')
except Exception as e:
    print(f'❌ Error: {e}')
PYTEST

# 4. Check backend health
curl https://wordbattle2.de/health

# 5. Check backend logs after restart
journalctl -u wordbattle-backend -f
# Or: tail -f /var/log/wordbattle.log
# Look for: "Firebase Admin initialized with credentials"
```

---

## 🚨 Troubleshooting

### Issue 1: "firebase_admin module not found"

**Solution**:
```bash
pip install firebase-admin==6.3.0
# Make sure you're in the correct virtual environment
source .venv/bin/activate
pip install firebase-admin==6.3.0
```

### Issue 2: "Failed to initialize Firebase Admin"

**Causes**:
1. Credentials file not found at specified path
2. Credentials file not readable (permission issue)
3. Invalid JSON in credentials file

**Solution**:
```bash
# Check file exists
ls -la /opt/wordbattle/config/firebase-credentials.json

# Check permissions
chmod 600 /opt/wordbattle/config/firebase-credentials.json
chown appuser:appuser /opt/wordbattle/config/firebase-credentials.json

# Validate JSON
python3 -c "import json; json.load(open('/opt/wordbattle/config/firebase-credentials.json'))"
```

### Issue 3: "Permission denied to send notification"

**Causes**:
1. Service account doesn't have "Firebase Cloud Messaging Admin" role
2. FCM API not enabled in Google Cloud

**Solution**:
1. Go to Firebase Console → Project Settings → Service Accounts
2. Click "Manage service account permissions" 
3. Add role: "Firebase Cloud Messaging Admin"
4. Enable FCM API in Google Cloud Console

### Issue 4: "Cannot reach fcm.googleapis.com"

**Causes**: Firewall blocking outbound HTTPS

**Solution**:
```bash
# Test connectivity
curl -I https://fcm.googleapis.com

# If blocked, allow outbound HTTPS
sudo ufw allow out 443/tcp
# Or update iptables accordingly
```

---

## 📖 Step-by-Step Installation Guide

### Complete Process for Self-Hosted Server:

```bash
# ============================================================
# STEP 1: LOCAL DEVELOPMENT MACHINE
# ============================================================

cd /Users/janbinge/git/wordbattle/wordbattle-backend

# Add Firebase dependency
echo "" >> requirements.txt
echo "# Push Notifications" >> requirements.txt
echo "firebase-admin==6.3.0" >> requirements.txt

# Commit changes
git add requirements.txt
git commit -m "Add Firebase Admin SDK for push notifications"
git push origin main

# ============================================================
# STEP 2: FIREBASE CONSOLE (Web Browser)
# ============================================================

# 1. Go to: https://console.firebase.google.com
# 2. Select or create "WordBattle" project
# 3. Project Settings → Service Accounts
# 4. Click "Generate New Private Key"
# 5. Download JSON file → Save as: wordbattle-firebase-adminsdk.json

# ============================================================
# STEP 3: UPLOAD TO SERVER
# ============================================================

# From local machine:
scp wordbattle-firebase-adminsdk.json user@wordbattle2.de:/tmp/

# ============================================================
# STEP 4: ON SERVER - SECURE CREDENTIALS
# ============================================================

ssh user@wordbattle2.de

# Create config directory
sudo mkdir -p /opt/wordbattle/config

# Move and secure credentials
sudo mv /tmp/wordbattle-firebase-adminsdk.json /opt/wordbattle/config/firebase-credentials.json
sudo chmod 600 /opt/wordbattle/config/firebase-credentials.json
sudo chown wordbattle:wordbattle /opt/wordbattle/config/firebase-credentials.json
# (Replace 'wordbattle' with your actual app user)

# ============================================================
# STEP 5: UPDATE BACKEND CODE
# ============================================================

cd /path/to/wordbattle-backend

# Pull latest changes
git pull origin main

# Install new dependencies
source .venv/bin/activate  # if using venv
pip install -r requirements.txt

# Verify installation
python3 -c "import firebase_admin; print('✅ Firebase Admin SDK installed')"

# ============================================================
# STEP 6: UPDATE ENVIRONMENT
# ============================================================

# Edit production environment file
nano .env  # or wherever your env vars are

# Add these lines:
# FIREBASE_CREDENTIALS_PATH=/opt/wordbattle/config/firebase-credentials.json
# ENABLE_PUSH_NOTIFICATIONS=true

# ============================================================
# STEP 7: RUN DATABASE MIGRATION
# ============================================================

# After implementing the migration script from the plan:
source .venv/bin/activate
alembic upgrade head

# Verify tables created
psql -U wordbattle_user -d wordbattle_prod -c "\dt push_*"
# Should show: push_tokens, notification_preferences, notification_log

# ============================================================
# STEP 8: RESTART BACKEND
# ============================================================

# Systemd:
sudo systemctl restart wordbattle-backend

# Docker:
docker-compose restart backend

# Manual:
pkill -f "uvicorn app.main:app"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /var/log/wordbattle.log 2>&1 &

# ============================================================
# STEP 9: VERIFY WORKING
# ============================================================

# Check health endpoint
curl https://wordbattle2.de/health

# Check logs for Firebase initialization
tail -100 /var/log/wordbattle.log | grep -i firebase
# Should see: "Firebase Admin initialized with credentials"

# Test notification endpoint (after implementing API)
curl -X POST https://wordbattle2.de/push/token \
  -H "Authorization: Bearer YOUR_TEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token":"test_fcm_token","platform":"ios","app_version":"1.0.6"}'

# Should return 201 Created

# ============================================================
# DONE! ✅
# ============================================================
```

---

## 🔍 Verification Checklist

After installation, verify:

- [ ] `pip list | grep firebase-admin` shows version 6.3.0
- [ ] Firebase credentials file exists at specified path
- [ ] File permissions are 600 (read/write for owner only)
- [ ] Environment variables set correctly
- [ ] Backend restarts without errors
- [ ] Logs show "Firebase Admin initialized"
- [ ] Health endpoint returns healthy
- [ ] Database tables created (push_tokens, etc.)
- [ ] Can connect to fcm.googleapis.com from server

---

## 💰 Cost Considerations

### Firebase Free Tier (Spark Plan):
- **FCM Messages**: Unlimited free
- **API Calls**: Generous free quota
- **Storage**: 1 GB free
- **Database**: Not needed for push notifications

### Recommendation:
Start with **free tier** - it's more than enough for WordBattle's scale.

**When to upgrade**: If you exceed 10 million messages/month (unlikely).

---

## 🎯 Summary

### To Add Push Notifications to Your Self-Hosted Server:

**Requirements**:
1. ✅ Add `firebase-admin==6.3.0` to requirements.txt
2. ✅ Upload Firebase credentials JSON to server
3. ✅ Add 2 environment variables
4. ✅ Run database migration
5. ✅ Restart backend

**What Changes**:
- Python packages: +1 (firebase-admin)
- Server files: +1 (credentials JSON)
- Environment variables: +2
- Database tables: +3
- Disk space: ~5 MB
- Memory: ~10-20 MB

**What Doesn't Change**:
- Nginx configuration: No changes
- PostgreSQL: Same database, just new tables
- Docker: Optional volume mount
- SSL/TLS: No changes
- Networking: Just outbound HTTPS (likely already allowed)

**Total Installation Time**: ~10 minutes (after you have Firebase credentials)

---

**Status**: Ready to install  
**Documentation**: Complete with troubleshooting  
**Next Step**: Generate Firebase credentials and follow installation guide

---

*This guide is specifically tailored for your self-hosted server setup.*
