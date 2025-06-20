# 🛡️ Deployment Safety Guide

## ❌ NEVER DO THESE:

1. **Never bypass the deployment script** with manual `gcloud run deploy` commands
2. **Never deploy directly to production** without testing first
3. **Never modify environment variables manually** in Cloud Run console
4. **Never commit sensitive data** like passwords to git

## ✅ ALWAYS DO THESE:

### 1. Use the Deployment Script
```bash
# Test changes first
./deploy-gcp-production.sh testing

# Only deploy to production after testing
./deploy-gcp-production.sh production
```

### 2. Create .env File First
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your actual credentials (never commit this file)
```

### 3. Test Before Production
```bash
# Deploy to testing environment
./deploy-gcp-production.sh testing

# Test the endpoints
curl https://wordbattle-backend-test-XXXXX.run.app/health

# Only then deploy to production
./deploy-gcp-production.sh production
```

### 4. Backup Working State
```bash
# Before making changes, save current working config
gcloud run services describe wordbattle-backend-prod --region=europe-west1 > backup-config.yaml
```

## 🚨 If Something Breaks:

### 1. Check Health Status
```bash
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/health
```

### 2. Check Database Status
```bash
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/database/status
```

### 3. Check Admin Status
```bash
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/admin/database/admin-status
```

### 4. Restore from Git
```bash
# Reset to last working commit
git log --oneline
git reset --hard <working-commit-hash>
./deploy-gcp-production.sh production
```

## 📋 Working Configuration Checklist

Before deploying, verify:
- [ ] Health endpoint returns `"status": "healthy"`
- [ ] Database status shows proper word counts
- [ ] Admin user `jan@binge.de` exists
- [ ] Email functionality works
- [ ] Admin endpoints accessible

## 🔧 Current Working Setup

**Production URL**: `https://wordbattle-backend-prod-441752988736.europe-west1.run.app`

**Database**: Cloud SQL PostgreSQL
- Instance: `wordbattle-1748668162:europe-west1:wordbattle-db`
- User: `postgres`
- Database: `wordbattle`

**Email**: SMTP via smtp.strato.de
- Username: `jan@binge-dev.de`
- Port: 465 (SSL)

**Admin User**: `jan@binge.de` (username: `jan_admin`)

## 🎯 Remember:
**Working is better than perfect. Never break a working production system for small improvements.** 