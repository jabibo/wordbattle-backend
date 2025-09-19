# ⚡ Quick Environment Switch Guide

## 🎯 **When you're ready to switch (after deployment)**

### **Step 1: Migrate Data** (5 minutes)
```bash
cd wordbattle-backend
python3 scripts/migrate-to-secure-dev.py --verbose
```

### **Step 2: Switch Frontend** (30 seconds)
```dart
// Edit: wordbattle-frontend/lib/config/environment_config.dart
// Line 12: Change to:
static const Environment currentEnvironment = Environment.secure;
```

### **Step 3: Test** (2 minutes)
```bash
cd wordbattle-frontend
flutter run
# Test login, game creation, gameplay
```

## 🚀 **That's it!**

You'll now be running on:
- **Backend**: `https://wordbattle-backend-dev-15814336315.europe-west1.run.app`
- **Security**: High (private networking, VPC)
- **Data**: Your production data in secure environment

## 🆘 **Quick Rollback**
If needed, just change the environment back:
```dart
static const Environment currentEnvironment = Environment.test;
```

## 📊 **Migration Script Details**

**Source**: `wordbattle-1748668162:wordbattle_test` (current working environment)  
**Target**: `wordbattle-secure:wordbattle_dev` (secure development)

**What gets migrated**:
- Users and authentication data
- Games and game states  
- Player records and scores
- Word dictionaries
- Chat messages
- Game invitations

**Safety features**:
- Dry-run mode for testing
- Comprehensive logging
- Data validation
- Error handling
- Connection management
