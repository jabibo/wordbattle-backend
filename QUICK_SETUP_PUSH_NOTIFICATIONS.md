# Push Notifications - Self-Hosted Quick Reference

## 🎯 What to Install on Your Server

### Single Python Package:
```bash
pip install firebase-admin==6.3.0
```

**That's it!** No other services needed.

---

## 📋 5-Minute Setup

```bash
# 1. Pull latest code
cd /path/to/wordbattle-backend
git pull

# 2. Install Firebase SDK
pip install -r requirements.txt

# 3. Add credentials file (get from Firebase Console)
# Upload firebase-credentials.json to server

# 4. Update .env
echo "FIREBASE_CREDENTIALS_PATH=/opt/wordbattle/config/firebase-credentials.json" >> .env
echo "ENABLE_PUSH_NOTIFICATIONS=true" >> .env

# 5. Restart backend
systemctl restart wordbattle-backend
```

---

## 🔑 Get Firebase Credentials

1. Go to: https://console.firebase.google.com
2. Select project (or create "WordBattle")
3. Project Settings → Service Accounts
4. Click "Generate New Private Key"
5. Download JSON file
6. Upload to server

---

## ✅ That's All!

**No need for**:
- ❌ Additional servers
- ❌ Docker changes
- ❌ Nginx reconfiguration
- ❌ New databases
- ❌ Port forwarding
- ❌ Firewall changes (outbound HTTPS usually allowed)

**Your existing infrastructure works perfectly!**

---

## 📚 Full Documentation

- **Complete Guide**: `PUSH_NOTIFICATIONS_SELF_HOSTED_SETUP.md`
- **Implementation Plan**: See frontend repository
- **Troubleshooting**: Included in complete guide

---

**Impact on Server**: Minimal (~5 MB disk, ~15 MB RAM)  
**Setup Time**: 10 minutes  
**Complexity**: Very Low
