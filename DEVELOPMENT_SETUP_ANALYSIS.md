# WordBattle Backend - Current Setup Analysis

**Date**: February 6, 2026  
**Analysis**: Development vs Production Environment

---

## 🔍 Current Setup Determination

### **Local Development (Your MacBook)**

✅ **Virtual Environment**: `.venv/` exists  
✅ **Development Mode**: Python virtual environment  
❌ **Docker NOT Running Locally**: Docker daemon not active  
📝 **Purpose**: Code development, testing, Git operations

### **Production (wordbattle2.de)**

✅ **Self-Hosted Server**: wordbattle2.de  
✅ **Likely Docker-based**: Based on documentation references  
✅ **PostgreSQL Database**: Self-hosted (not Cloud SQL)  
✅ **Cloud Provider Config**: `CLOUD_PROVIDER=self-hosted`  

---

## 🎯 Development vs Production Setup

### **Two Separate Environments:**

```
┌─────────────────────────────────────────────┐
│ LOCAL DEVELOPMENT (Your MacBook)           │
├─────────────────────────────────────────────┤
│ • Python virtual environment (.venv/)      │
│ • No Docker containers running             │
│ • Git repository for code changes          │
│ • Code editing and testing                 │
│ • NOT where push notifications run         │
└─────────────────────────────────────────────┘
                    ↓ git push
                    ↓
┌─────────────────────────────────────────────┐
│ PRODUCTION SERVER (wordbattle2.de)         │
├─────────────────────────────────────────────┤
│ • Self-hosted infrastructure               │
│ • Docker containers (likely)               │
│ • PostgreSQL database                      │
│ • FastAPI backend running 24/7             │
│ • WHERE push notifications will run        │
└─────────────────────────────────────────────┘
```

---

## 📦 Firebase Admin SDK Installation Strategy

### **Option A: Install in Virtual Environment (Local Development)**

**Purpose**: Local testing and development

```bash
cd /Users/janbinge/git/wordbattle/wordbattle-backend
source .venv/bin/activate
pip install firebase-admin==6.3.0

# Test locally
uvicorn app.main:app --reload
```

**Pros**: Test push notifications locally  
**Cons**: Need Firebase credentials on your MacBook  
**Use Case**: Development and testing before production deployment

---

### **Option B: Install on Production Server (Self-Hosted)**

**Purpose**: Production push notifications

**This is where it MUST be installed for production use.**

```bash
# On wordbattle2.de server:

# If using Docker (recommended):
# Firebase Admin SDK is installed via requirements.txt when Docker image builds
# Just need to rebuild Docker image after updating requirements.txt

docker-compose build backend
docker-compose up -d backend

# If NOT using Docker (direct Python):
pip install firebase-admin==6.3.0
systemctl restart wordbattle-backend
```

---

## 🐳 Determining If Server Uses Docker

### **Evidence of Docker-Based Production:**

1. ✅ `Dockerfile.cloudrun` exists (for containerized deployment)
2. ✅ `docker-compose.yml` exists (for local Docker setup)
3. ✅ Documentation mentions "Docker containers"
4. ✅ Deployment uses Docker images
5. ✅ Cloud Run deployment (which uses containers)

### **Most Likely Production Setup on wordbattle2.de:**

**Scenario 1: Docker Compose** (Most Likely)
```
wordbattle2.de:
├── docker-compose.yml
├── Backend container (FastAPI)
└── Database container (PostgreSQL)
```

**Scenario 2: Direct Docker** (Possible)
```
wordbattle2.de:
├── Docker container running backend
└── Separate PostgreSQL container
```

**Scenario 3: Systemd Service** (Less Likely)
```
wordbattle2.de:
├── systemd service running uvicorn
└── PostgreSQL installed directly
```

---

## ✅ RECOMMENDED APPROACH

Since I cannot directly check your server, here's a **universal installation guide** that works for all scenarios:

### **Step 1: Update requirements.txt (DONE ✅)**

Already committed:
```python
firebase-admin==6.3.0
```

### **Step 2: Deploy to Server**

```bash
# From your local machine
cd /Users/janbinge/git/wordbattle/wordbattle-backend

# Commit is already done, so just deploy based on your current method:
```

**If your server uses DOCKER** (most likely):
```bash
# SSH to server
ssh user@wordbattle2.de

# Navigate to backend
cd /path/to/wordbattle-backend

# Pull latest code
git pull

# Rebuild Docker image (installs firebase-admin)
docker-compose build backend

# Upload Firebase credentials
mkdir -p /opt/wordbattle/config
# (Upload firebase-credentials.json here)

# Update docker-compose.yml to mount credentials
nano docker-compose.yml
# Add volume:
#   - /opt/wordbattle/config/firebase-credentials.json:/app/config/firebase-credentials.json:ro

# Add environment variables
nano .env  # or docker-compose.yml
# FIREBASE_CREDENTIALS_PATH=/app/config/firebase-credentials.json
# ENABLE_PUSH_NOTIFICATIONS=true

# Restart
docker-compose up -d backend

# Verify
docker-compose logs -f backend
# Look for: "Firebase Admin initialized with credentials"
```

**If your server uses SYSTEMD** (direct Python):
```bash
# SSH to server
ssh user@wordbattle2.de

# Navigate to backend
cd /path/to/wordbattle-backend
git pull

# Install in Python environment
source venv/bin/activate  # or wherever your venv is
pip install -r requirements.txt

# Add credentials and environment variables
# (same as Docker approach)

# Restart service
sudo systemctl restart wordbattle-backend
```

---

## 🔍 How to Determine Your Server Setup

### **Method 1: Check from local machine**

```bash
# Try to check via SSH (update with your credentials)
ssh user@wordbattle2.de "which docker && docker ps || echo 'Docker not found'; systemctl status wordbattle-backend 2>/dev/null || echo 'No systemd service'"
```

### **Method 2: Check deployment scripts**

Your deployment scripts show you're using **Google Cloud Run**, which means:
- ✅ Docker-based deployment
- ✅ Uses `Dockerfile.cloudrun`
- ✅ Containers deployed to Cloud Run

**However**, the environment config shows `CLOUD_PROVIDER=self-hosted`, suggesting you **migrated from GCP to self-hosted**.

---

## 🎯 CONCLUSION & RECOMMENDATION

### **Most Likely Scenario:**

You're using **Docker-based deployment** on your self-hosted server (wordbattle2.de), based on:
- Docker files in repository
- docker-compose.yml configuration
- Migration documentation from GCP to self-hosted
- CLOUD_PROVIDER=self-hosted setting

### **Recommended Installation Path:**

1. **Local (Your MacBook)**: 
   - ✅ Already done: `firebase-admin==6.3.0` in requirements.txt
   - Optional: Install locally for testing

2. **Production Server (wordbattle2.de)**:
   - ✅ Pull latest code: `git pull`
   - ✅ Rebuild Docker image: `docker-compose build` (installs firebase-admin)
   - ✅ Add Firebase credentials: Upload JSON file
   - ✅ Update environment: Add 2 variables
   - ✅ Restart: `docker-compose restart backend`

---

## 📋 Next Actions

1. **Determine exact server setup** (5 minutes):
   ```bash
   ssh user@wordbattle2.de "docker ps; systemctl list-units | grep wordbattle"
   ```

2. **Choose installation method** based on result:
   - If Docker: Follow Docker instructions
   - If Systemd: Follow direct Python instructions

3. **Proceed with installation** using appropriate method

---

## 📚 All Documentation Ready

- **`PUSH_NOTIFICATIONS_SELF_HOSTED_SETUP.md`** - Complete step-by-step guide (both Docker & Systemd)
- **`QUICK_SETUP_PUSH_NOTIFICATIONS.md`** - 5-minute quick reference
- Both committed to repository and ready to use

---

**Status**: Ready to install once server setup is confirmed  
**Next Step**: Determine if server uses Docker or direct Python
