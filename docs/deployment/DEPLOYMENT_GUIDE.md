# WordBattle Backend - Deployment Guide

## 🚀 Multi-Environment Deployment with Git Integration

This guide explains how to deploy your WordBattle backend to Google Cloud Platform with proper environment separation and Git workflow integration.

## 📋 Overview

Your deployment system now supports:
- **Two environments**: Production and Testing
- **Git integration**: Automatic commit tracking and tagging
- **Environment-specific configurations**: Different resources and settings per environment
- **Automated testing**: Health checks and verification
- **Deployment tracking**: Git tags for production releases

## 🏗️ Infrastructure Layout

### Production Environment
- **Service Name**: `wordbattle-backend-prod`
- **Resources**: 2 CPU cores, 2GB RAM
- **Scaling**: 1-100 instances (always-on)
- **Git Requirements**: Clean working directory required
- **Tagging**: Automatic Git tags created for tracking

### Testing Environment
- **Service Name**: `wordbattle-backend-test`
- **Resources**: 1 CPU core, 1GB RAM
- **Scaling**: 0-10 instances (cost-optimized)
- **Git Requirements**: Allows uncommitted changes
- **Tagging**: No automatic tags

## 🖥️ Deployment Commands

### Windows (PowerShell)

```powershell
# Deploy to production (current branch)
.\deploy-gcp-production.ps1

# Deploy to testing
.\deploy-gcp-production.ps1 -Environment testing

# Deploy specific branch to production
.\deploy-gcp-production.ps1 -Environment production -GitBranch main

# Deploy to testing with specific branch
.\deploy-gcp-production.ps1 -Environment testing -GitBranch feature/new-api

# Skip Git checks (emergency deployment)
.\deploy-gcp-production.ps1 -SkipGitCheck
```

### Linux/Mac (Bash)

```bash
# Deploy to production (current branch)
./deploy-gcp-production.sh

# Deploy to testing
./deploy-gcp-production.sh testing

# Deploy specific branch to production
./deploy-gcp-production.sh production main

# Deploy to testing with specific branch
./deploy-gcp-production.sh testing feature/new-api

# Skip Git checks (emergency deployment)
./deploy-gcp-production.sh production '' --skip-git-check
```

## 🔄 Git Workflow Integration

### Automatic Git Operations

1. **Repository Check**: Verifies you're in a Git repository
2. **Branch Management**: Switches to target branch if needed
3. **Clean Check**: Ensures clean working directory for production
4. **Pull Updates**: Fetches latest changes from remote
5. **Commit Tracking**: Includes Git commit in image tags and environment variables
6. **Production Tagging**: Creates timestamped Git tags for production deployments

### Git Information in Deployments

Each deployment includes:
- **Docker Image Tags**: `prod-abc1234` or `test-abc1234` (using Git commit hash)
- **Environment Variables**: `GIT_COMMIT`, `GIT_BRANCH`, `DEPLOY_TIMESTAMP`
- **Docker Labels**: Full Git metadata attached to images
- **Production Tags**: Automatic Git tags like `deploy-prod-20241206-143022`

## 🎯 Environment-Specific Features

### Production Environment

```bash
# Strict requirements
✅ Clean working directory required
✅ Always-on with minimum 1 instance
✅ High performance resources
✅ Automatic Git tagging
✅ Optimized for stability
```

### Testing Environment

```bash
# Flexible for development
✅ Allows uncommitted changes
✅ Scales to 0 when idle (cost-saving)
✅ Debug mode enabled
✅ Basic resources for testing
✅ No automatic Git tags
```

## 📊 Deployment Process

### 1. Git Integration Check
```
🔍 Git Integration Check...
  Current branch: feature/new-api
  Target branch: feature/new-api
  ✅ Working directory is clean
  Pulling latest changes from origin/feature/new-api...
  Commit: abc1234
  Message: Add new API endpoint
  Author: Developer Name
  Date: 2024-12-06 14:30:22 +0100
✅ Git integration check passed
```

### 2. Environment Configuration
```
Configuration:
  Project: wordbattle-1748668162
  Environment: production
  Service: wordbattle-backend-prod
  Region: europe-west1
  Image: wordbattle-backend:prod-abc1234
  Resources: 2 CPU, 2Gi RAM
  Scaling: 1-100 instances
  Git Commit: abc1234 (main)
```

### 3. Docker Build & Push
```
Building Docker image for production environment...
  Including Git commit: abc1234
✅ Docker image built successfully
✅ Image pushed to GCR successfully
```

### 4. Cloud Run Deployment
```
Deploying to Google Cloud Run (production environment)...
Creating new Cloud Run service: wordbattle-backend-prod
✅ Deployment successful!
Creating Git tag: deploy-prod-20241206-143022
✅ Git tag created and pushed
```

### 5. Testing & Verification
```
Testing deployment...
Testing health endpoint...
✅ Health check passed!
Testing API documentation...
✅ API documentation accessible!
```

## 🌐 Current Live URLs

After successful deployment, you'll have:

### Production Environment
- **Application**: https://wordbattle-backend-prod-[hash].europe-west1.run.app
- **API Docs**: https://wordbattle-backend-prod-[hash].europe-west1.run.app/docs
- **Health Check**: https://wordbattle-backend-prod-[hash].europe-west1.run.app/health

### Testing Environment  
- **Application**: https://wordbattle-backend-test-[hash].europe-west1.run.app
- **API Docs**: https://wordbattle-backend-test-[hash].europe-west1.run.app/docs
- **Health Check**: https://wordbattle-backend-test-[hash].europe-west1.run.app/health

## 🛠️ Development Workflow

### Recommended Git Workflow

1. **Feature Development**
   ```bash
   # Create feature branch
   git checkout -b feature/new-functionality
   
   # Deploy to testing for development
   ./deploy-gcp-production.sh testing
   ```

2. **Testing Phase**
   ```bash
   # Test with uncommitted changes
   ./deploy-gcp-production.sh testing
   
   # Commit when ready
   git commit -m "Add new functionality"
   ```

3. **Production Release**
   ```bash
   # Merge to main
   git checkout main
   git merge feature/new-functionality
   
   # Deploy to production (creates Git tag)
   ./deploy-gcp-production.sh production
   ```

### Emergency Deployments

If you need to deploy without Git checks:
```bash
# Skip all Git validation
./deploy-gcp-production.sh production '' --skip-git-check
```

## 📈 Monitoring & Management

### View Deployment Logs
```bash
# Production logs
gcloud run services logs tail wordbattle-backend-prod --region=europe-west1

# Testing logs
gcloud run services logs tail wordbattle-backend-test --region=europe-west1
```

### Check Service Status
```bash
# Production status
gcloud run services describe wordbattle-backend-prod --region=europe-west1

# Testing status
gcloud run services describe wordbattle-backend-test --region=europe-west1
```

### View Git Tags
```bash
# List deployment tags
git tag -l "deploy-prod-*"

# Show tag details
git show deploy-prod-20241206-143022
```

## 🔧 Troubleshooting

### Common Issues

1. **Git Repository Not Found**
   ```
   ❌ Not in a Git repository or Git not installed
   Solution: Run from project root or use --skip-git-check
   ```

2. **Uncommitted Changes in Production**
   ```
   ❌ Production deployments require clean working directory
   Solution: Commit or stash changes, or deploy to testing first
   ```

3. **Branch Switch Failed**
   ```
   ❌ Failed to switch to branch: feature/xyz
   Solution: Check if branch exists and you have permissions
   ```

4. **Docker Build Failed**
   ```
   ❌ Docker build failed
   Solution: Check Dockerfile.cloudrun and ensure Docker is running
   ```

### Recovery Commands

```bash
# Reset to clean state
git checkout main
git pull origin main

# Force deployment without Git
./deploy-gcp-production.sh production '' --skip-git-check

# Check current deployments
gcloud run services list --region=europe-west1
```

## 🔐 Security & Best Practices

1. **Production Deployments**
   - Always use clean Git state
   - Deploy from main/production branch
   - Let the system create Git tags automatically

2. **Testing Deployments**
   - Use for feature testing
   - Can deploy uncommitted changes
   - Always test before production

3. **Branch Management**
   - Use feature branches for development
   - Merge to main for production releases
   - Keep main branch stable

4. **Environment Variables**
   - Production: Optimized for performance and stability
   - Testing: Debug mode enabled for development

---

## 🎉 Success!

Your WordBattle backend now has a professional deployment pipeline with:
- ✅ Git-integrated deployment tracking
- ✅ Separate production and testing environments
- ✅ Automatic tagging and version control
- ✅ Environment-specific optimizations
- ✅ Comprehensive testing and verification

Happy deploying! 🚀 