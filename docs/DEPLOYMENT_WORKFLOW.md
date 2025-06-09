# WordBattle Backend - Deployment Workflow

This document outlines the proper deployment workflow for the WordBattle backend.

## 🔄 Deployment Workflow

### 1. Development Workflow
```bash
# 1. Make your changes locally
git add .
git commit -m "Your descriptive commit message"

# 2. Push to repository  
git push origin main

# 3. Deploy to test environment
./deploy-test.sh

# 4. Test functionality in test environment
curl https://wordbattle-backend-test-441752988736.europe-west1.run.app/health

# 5. If tests pass, deploy to production
./deploy-production.sh
```

### 2. Production Deployment Safeguards

The production deployment script includes several safeguards:

✅ **Git State Checks**:
- Ensures no uncommitted changes
- Ensures local branch is in sync with remote
- Can be bypassed with `--force` flag (not recommended)

✅ **Deployment Tagging**:
- Automatically creates git tags for each deployment
- Format: `deploy-prod-YYYYMMDD-HHMMSS`
- Includes commit hash and message
- Tags are pushed to remote repository

✅ **Environment Configuration**:
- Production-specific environment variables
- Secure secret key generation
- Database and email configuration

### 3. Test Environment

The test environment is more permissive:
- Allows uncommitted changes (for testing)
- Creates local tags only (doesn't push to remote)
- Uses separate service name and configuration

## 📋 Available Scripts

### `./deploy-production.sh`
- Deploys to production environment
- Requires clean git state
- Creates and pushes deployment tags
- Full production configuration

### `./deploy-test.sh`  
- Deploys to test environment
- Allows uncommitted changes
- Local tagging only
- Test configuration

### `./switch-environment.sh`
- Utility to switch between environments
- Updates local environment variables
- Shows current environment status

## 🏷️ Git Tags and Versioning

### Deployment Tags
- **Production**: `deploy-prod-YYYYMMDD-HHMMSS`
- **Test**: `deploy-test-YYYYMMDD-HHMMSS` (local only)

### Viewing Deployment History
```bash
# View all production deployment tags
git tag | grep deploy-prod

# View latest production deployments
git tag | grep deploy-prod | tail -10

# View deployment details
git show deploy-prod-20250609-173000
```

## 🚨 Emergency Procedures

### Force Deployment (Not Recommended)
```bash
# Deploy with uncommitted changes (emergency only)
./deploy-production.sh --force
```

### Rollback to Previous Version
```bash
# 1. Find the previous deployment tag
git tag | grep deploy-prod | tail -5

# 2. Checkout the previous version
git checkout deploy-prod-YYYYMMDD-HHMMSS

# 3. Deploy the previous version
./deploy-production.sh --force

# 4. Return to main branch
git checkout main
```

## 🔧 Environment Configuration

### Production Environment
- **Service**: `wordbattle-backend-prod`
- **Database**: Cloud SQL PostgreSQL (`wordbattle_db`)
- **Email**: SMTP configuration
- **CORS**: Configured for mobile app

### Test Environment  
- **Service**: `wordbattle-backend-test`
- **Database**: Cloud SQL PostgreSQL (`wordbattle_test`)
- **Email**: Same SMTP (test emails)
- **CORS**: Same as production

**Database Separation**: Test and production use separate databases (`wordbattle_test` vs `wordbattle_db`) on the same Cloud SQL instance for proper data isolation.

## 📊 Monitoring Deployments

### Health Checks
```bash
# Production health
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/health

# Test health  
curl https://wordbattle-backend-test-441752988736.europe-west1.run.app/health

# Admin status
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/admin/database/admin-status
```

### Deployment Verification
Each deployment script automatically tests:
- Basic endpoint response
- Health endpoint
- Admin endpoints
- Service availability

## 🔐 Security Considerations

1. **Secret Management**: Secrets are generated per deployment
2. **Git History**: All deployments are tracked in git tags
3. **Environment Separation**: Production and test are isolated
4. **Access Control**: Cloud Run IAM controls deployment access

## 📚 Best Practices

1. **Always test first**: Deploy to test environment before production
2. **Meaningful commits**: Use descriptive commit messages
3. **Tag releases**: Production deployments are automatically tagged
4. **Monitor deployments**: Check health endpoints after deployment
5. **Keep git clean**: Avoid force deployments when possible

---

## 🆘 Troubleshooting

### Common Issues

**"Uncommitted changes" error**:
```bash
git add .
git commit -m "Your changes"
git push origin main
./deploy-production.sh
```

**"Branch not in sync" error**:
```bash
git pull origin main  # or git push origin main
./deploy-production.sh
```

**Deployment failure**:
```bash
# Check the build logs in Google Cloud Console
# Or retry deployment
./deploy-production.sh
``` 