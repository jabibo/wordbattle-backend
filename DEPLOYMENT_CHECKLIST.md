# 🚀 WordBattle Deployment & Environment Switch Checklist

## 📋 **Pre-Deployment Checklist**

### **1. Current State Verification** ✅
- [x] Frontend pointing to test environment (`test-441...`)
- [x] Test database contains production data (migrated)
- [x] All recent fixes deployed and working
- [x] Secure environment configuration added to frontend

### **2. Backend Status Check**
```bash
# Check current backend health
curl -s https://wordbattle-backend-test-441752988736.europe-west1.run.app/health | jq
curl -s https://wordbattle-backend-prod-skhco4fxoq-ew.a.run.app/health | jq

# Verify secure environment
curl -s https://wordbattle-backend-dev-15814336315.europe-west1.run.app/health | jq
```

### **3. Code Status Check**
```bash
# Backend
cd wordbattle-backend
git status
git log --oneline -3

# Frontend  
cd ../wordbattle-frontend
git status
git log --oneline -3
```

---

## 🚀 **Current Deployment (Today)**

### **Deploy Current Version**
```bash
# Deploy backend testing (if needed)
cd wordbattle-backend
./deploy-unified.sh testing

# Deploy backend production (if needed)
./deploy-unified.sh production
```

### **Verify Deployment**
- [ ] Test environment working: `test-441...`
- [ ] Production environment working: `prod-skhco...`
- [ ] Frontend connects successfully
- [ ] Game creation/joining works
- [ ] Letter scoring correct (German: Ö=8, Ä=6, Ü=6)

---

## 🔄 **Environment Switch (After Deployment)**

### **Phase 1: Data Migration to Secure**
```bash
cd wordbattle-backend

# 1. Preview migration (dry run)
python3 scripts/migrate-to-secure-dev.py --dry-run --verbose

# 2. Run actual migration
python3 scripts/migrate-to-secure-dev.py --verbose

# 3. Verify migration completed
# Check logs for success message
```

### **Phase 2: Frontend Switch**
```dart
// Edit: wordbattle-frontend/lib/config/environment_config.dart
// Change line 12:
static const Environment currentEnvironment = Environment.secure;
```

### **Phase 3: Test Secure Environment**
```bash
cd wordbattle-frontend
flutter run

# Test these features:
# - Login/authentication
# - Game creation 
# - Player invitation
# - Game play (moves, scoring)
# - Previous opponents
# - Real-time updates
```

---

## 🔍 **Verification Steps**

### **Backend Health Checks**
- [ ] **Current Test**: `https://wordbattle-backend-test-441752988736.europe-west1.run.app/health`
- [ ] **Current Prod**: `https://wordbattle-backend-prod-skhco4fxoq-ew.a.run.app/health`  
- [ ] **Secure Dev**: `https://wordbattle-backend-dev-15814336315.europe-west1.run.app/health`

### **Database Connectivity**
```bash
# Check migration results
python3 -c "
import sys
sys.path.append('.')
from scripts.migrate_to_secure_dev import SecureEnvironmentMigrator
migrator = SecureEnvironmentMigrator()
migrator.connect_databases()
print('✅ Secure environment databases accessible')
"
```

### **Frontend Features**
- [ ] Authentication (email login)
- [ ] Game creation with player search
- [ ] Game auto-start when players join
- [ ] Tile placement and scoring
- [ ] Pass/exchange functionality  
- [ ] Previous opponents display
- [ ] Real-time game synchronization

---

## 📊 **Environment Comparison**

| Feature | Current (Test) | Secure (Target) | Status |
|---------|---------------|-----------------|---------|
| **Backend URL** | `test-441...` | `dev-158...` | ✅ Ready |
| **Database** | `wordbattle_test` | `wordbattle_dev` | 🔄 Will migrate |
| **Security Level** | Medium | High | ⬆️ Upgrade |
| **Data** | Production copy | Will copy | 🔄 Migration ready |
| **Frontend Config** | Active | Ready | ✅ Configured |

---

## 🆘 **Rollback Plan**

If issues occur with secure environment:

```dart
// Quick rollback - change environment_config.dart back to:
static const Environment currentEnvironment = Environment.test;
```

This immediately reverts to the working test environment.

---

## 📝 **Migration Scripts Ready**

- ✅ `scripts/migrate-to-secure-dev.py` - Data migration tool
- ✅ Dry-run mode for testing
- ✅ Comprehensive logging
- ✅ Safety checks and validation
- ✅ Error handling and rollback

---

## 🎯 **Benefits After Switch**

- **🛡️ Enhanced Security**: Private networking, VPC isolation
- **🔒 Secure Data**: Production data in secure environment  
- **🧪 Safe Development**: Test with real data securely
- **🚀 Future Ready**: Infrastructure ready for secure production
- **💰 Cost Efficient**: Separate secure project billing

---

**Ready for deployment and environment switch! 🚀**
