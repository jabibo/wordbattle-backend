# Deployment Scripts Reference

Quick reference guide for all deployment scripts and utilities.

## 📋 Available Scripts

### `./deploy-production.sh`
**Purpose**: Deploy to production environment from main branch

**Requirements**:
- Clean git state (no uncommitted changes)
- Must be in sync with remote origin
- Automatically creates deployment tags

**Usage**:
```bash
# Standard production deployment
./deploy-production.sh

# Force deployment (emergency only)
./deploy-production.sh --force
```

**What it does**:
- ✅ Validates git state
- 🏷️ Creates deployment tag (`deploy-prod-YYYYMMDD-HHMMSS`)
- 🚀 Deploys to `wordbattle-backend-prod`
- 🗄️ Connects to `wordbattle_db` database
- 📧 Configures production SMTP
- 🧪 Runs health checks
- 📤 Pushes deployment tag to remote

---

### `./deploy-test.sh [branch]`
**Purpose**: Deploy to test environment

**Requirements**:
- None (allows uncommitted changes)
- Optional: specify branch name

**Usage**:
```bash
# Deploy current branch/changes
./deploy-test.sh

# Deploy specific branch
./deploy-test.sh feature/new-feature
./deploy-test.sh test
./deploy-test.sh main

# Deploy and return to current branch
./deploy-test.sh feature/testing && git checkout main
```

**What it does**:
- 🌿 Optionally switches to specified branch
- 🏷️ Creates local deployment tag (`deploy-test-YYYYMMDD-HHMMSS`)
- 🚀 Deploys to `wordbattle-backend-test`
- 🗄️ Connects to `wordbattle_test` database
- 📧 Configures test SMTP
- 🧪 Runs health checks

---

### `./switch-environment.sh`
**Purpose**: Utility to view and switch environment context

**Usage**:
```bash
# View current environment status
./switch-environment.sh

# Switch context (updates local environment variables)
./switch-environment.sh production
./switch-environment.sh test
```

**What it shows**:
- Current git branch and status
- Environment URLs
- Database connections
- Recent deployment tags

---

## 🔧 Deployment Workflow Examples

### Standard Development Cycle
```bash
# 1. Develop
git add .
git commit -m "Add new feature"
git push origin main

# 2. Test
./deploy-test.sh

# 3. Verify test environment
curl https://wordbattle-backend-test-441752988736.europe-west1.run.app/health

# 4. Deploy to production
./deploy-production.sh
```

### Feature Branch Development
```bash
# 1. Create feature branch
git checkout -b feature/admin-improvements

# 2. Develop and commit
git add .
git commit -m "Improve admin dashboard"
git push origin feature/admin-improvements

# 3. Test feature branch
./deploy-test.sh feature/admin-improvements

# 4. Merge to main when ready
git checkout main
git merge feature/admin-improvements
git push origin main

# 5. Deploy to production
./deploy-production.sh
```

### Hotfix Deployment
```bash
# 1. Create hotfix from main
git checkout main
git checkout -b hotfix/critical-fix

# 2. Fix and test quickly
git commit -m "Fix critical issue"
./deploy-test.sh hotfix/critical-fix

# 3. Verify fix works
curl https://test-url.com/health

# 4. Deploy to production immediately
git checkout main
git merge hotfix/critical-fix
git push origin main
./deploy-production.sh
```

### Collaborative Testing
```bash
# Team member A: Test their feature
./deploy-test.sh feature/user-profiles

# Team member B: Test their feature
./deploy-test.sh feature/game-improvements

# Combine features for integration testing
git checkout -b integration-test
git merge feature/user-profiles
git merge feature/game-improvements
./deploy-test.sh integration-test
```

## 🏷️ Deployment Tags

### Viewing Deployment History
```bash
# View all production deployments
git tag | grep deploy-prod

# View recent production deployments
git tag | grep deploy-prod | tail -10

# View deployment details
git show deploy-prod-20250609-173000

# View all test deployments (local only)
git tag | grep deploy-test
```

### Rollback to Previous Deployment
```bash
# 1. Find previous deployment
git tag | grep deploy-prod | tail -5

# 2. Checkout previous version
git checkout deploy-prod-20250609-150000

# 3. Deploy previous version
./deploy-production.sh --force

# 4. Return to main (or create fix)
git checkout main
```

## 🚨 Emergency Procedures

### Force Production Deployment
```bash
# Only use in emergencies!
./deploy-production.sh --force
```

### Quick Status Check
```bash
# Production health
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/health

# Test health
curl https://wordbattle-backend-test-441752988736.europe-west1.run.app/health

# Admin status
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/admin/database/admin-status
```

### Environment Recovery
```bash
# If test environment is broken
./deploy-test.sh main

# If production needs immediate rollback
git checkout deploy-prod-YYYYMMDD-HHMMSS
./deploy-production.sh --force
git checkout main
```

## 📊 Script Output Explanation

### Successful Deployment
```
🚀 Deploying WordBattle Backend to Production...
📋 Deployment Info:
   🏷️  Tag: deploy-prod-20250609-173000
   🔗 Commit: abc123d
   📝 Message: Add new admin endpoints
🔐 Generating secure SECRET_KEY...
✅ SECRET_KEY generated: xyz...
📦 Building and deploying service...
✅ Production deployment completed!
🏷️  Pushing deployment tag to remote...
🧪 Testing deployment...
✅ Basic endpoint test passed
✅ Health endpoint test passed
🎉 Production deployment successful!
```

### Error Examples
```
⚠️  WARNING: You have uncommitted changes!
⚠️  WARNING: Your branch is not in sync with origin!
❌ Basic endpoint test failed
❌ Deployment failed - check build logs
```

## 🔍 Troubleshooting

### Common Issues and Solutions

**"Uncommitted changes" error**:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

**"Branch not in sync" error**:
```bash
git pull origin main  # or git push origin main
```

**Build failures**:
- Check Google Cloud Console build logs
- Verify Dockerfile syntax
- Check environment variables

**Health check failures**:
- Check service logs in Cloud Run console
- Verify database connectivity
- Check environment configuration 