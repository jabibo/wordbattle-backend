# Development Workflow Guide

## 🔄 **Branch Strategy**

### **Branches**
- `main` - Production-ready code, manually deployed to production
- `test-environment` - Integration testing, automatically deployed to GCP testing environment

### **Workflow Process**

```
Feature Development → test-environment → Testing → main → Production
```

## 🧪 **Test Environment (Automated)**

### **Branch**: `test-environment`
**Purpose**: Integration testing and validation before production

**Auto-deploys to**: GCP Testing Environment
- **URL**: `https://wordbattle-backend-test-441752988736.europe-west1.run.app`
- **Environment**: Testing
- **Resources**: 1 CPU, 1GB RAM (cost-optimized)
- **Scaling**: 0-10 instances

### **Triggers**
- ✅ Push to `test-environment` branch
- ✅ Pull requests to `test-environment` branch

### **What happens automatically**:
1. **Run Tests**: Unit tests, linting, security scanning
2. **Build & Deploy**: Docker image built and deployed to GCP
3. **Validate**: Health checks, API tests, CORS validation
4. **Report**: Deployment summary with all test results

## 🏭 **Production Environment (Manual)**

### **Branch**: `main`
**Purpose**: Stable, production-ready releases

**Manual deploy with**: `./deploy-gcp-production.ps1 -Environment production`
- **Environment**: Production
- **Resources**: 2 CPU, 2GB RAM (high-performance)
- **Scaling**: 1-100 instances (always-on)

## 🛠️ **Development Process**

### **1. Feature Development**
```bash
# Create feature branch from test-environment
git checkout test-environment
git pull origin test-environment
git checkout -b feature/your-feature-name

# Develop your feature
# ... make changes ...

# Test locally
python -m pytest tests/
./deploy-gcp-production.ps1 -Environment testing  # Optional local testing
```

### **2. Integration Testing**
```bash
# Merge to test-environment for automated testing
git checkout test-environment
git pull origin test-environment
git merge feature/your-feature-name
git push origin test-environment

# 🤖 GitHub Actions automatically:
# - Runs all tests
# - Deploys to GCP testing environment
# - Validates deployment
# - Reports results
```

### **3. Production Release**
```bash
# After testing passes, merge to main
git checkout main
git pull origin main
git merge test-environment
git push origin main

# Manual production deployment
./deploy-gcp-production.ps1 -Environment production
```

## 🔧 **CORS Configuration**

Both environments are configured for `binge-dev.de`:

### **Testing Environment**
- ✅ `https://binge-dev.de`
- ✅ `https://localhost:3000`
- ✅ `http://localhost:3000`

### **Production Environment**
- ✅ `https://binge-dev.de`
- ✅ `https://localhost:3000`

## 📋 **Prerequisites for GitHub Actions**

### **Required GitHub Secrets**
You need to set up the following secret in your GitHub repository:

1. **Go to**: GitHub repo → Settings → Secrets and variables → Actions
2. **Add secret**: `GCP_SA_KEY`
   - **Value**: Service Account JSON key with Cloud Run permissions

### **Creating GCP Service Account**
```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --description="GitHub Actions deployment" \
  --display-name="GitHub Actions"

# Grant necessary permissions
gcloud projects add-iam-policy-binding wordbattle-1748668162 \
  --member="serviceAccount:github-actions@wordbattle-1748668162.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding wordbattle-1748668162 \
  --member="serviceAccount:github-actions@wordbattle-1748668162.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding wordbattle-1748668162 \
  --member="serviceAccount:github-actions@wordbattle-1748668162.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@wordbattle-1748668162.iam.gserviceaccount.com

# Copy the content of github-actions-key.json to GitHub secret GCP_SA_KEY
```

## 🚀 **Quick Commands**

### **Deploy to Testing (Manual)**
```bash
./deploy-gcp-production.ps1 -Environment testing
```

### **Deploy to Production (Manual)**
```bash
./deploy-gcp-production.ps1 -Environment production
```

### **Check Deployment Status**
```bash
# Testing environment
gcloud run services describe wordbattle-backend-test --region=europe-west1

# Production environment
gcloud run services describe wordbattle-backend-prod --region=europe-west1
```

## 🔍 **Monitoring & Logs**

### **Testing Environment**
- **Health**: `https://wordbattle-backend-test-441752988736.europe-west1.run.app/health`
- **API Docs**: `https://wordbattle-backend-test-441752988736.europe-west1.run.app/docs`
- **Logs**: Check GitHub Actions workflow results

### **Production Environment**
- **Manual deployment results**
- **GCP Console logs**

## ✅ **Benefits of This Workflow**

1. **Automated Testing**: Every push to `test-environment` runs full test suite
2. **Safe Integration**: Test changes before they reach production
3. **CORS Validation**: Automatic verification that `binge-dev.de` works
4. **Visual Feedback**: GitHub provides clear deployment status
5. **Rollback Ready**: Easy to revert if issues are found
6. **Cost Efficient**: Testing environment scales to zero when not used

## 🎯 **Next Steps**

1. Set up the GCP service account and GitHub secret
2. Push a test change to `test-environment` branch
3. Verify automatic deployment works
4. Use this workflow for all future development! 