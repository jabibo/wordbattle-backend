# WordBattle Backend Deployment Configuration

This document outlines the complete deployment process using the unified deployment script and the required environment configuration for the WordBattle backend.

## Overview

The WordBattle backend uses a unified deployment script (`deploy-unified.sh`) that supports three environments:
- **Production**: `wordbattle-backend-prod` (project: `wordbattle-secure`)
- **Development**: `wordbattle-backend-dev` (project: `wordbattle-secure`)
- **Testing**: `wordbattle-backend-test` (project: `wordbattle-secure`)

## Quick Start

### Prerequisites

1. **Docker** installed and running
2. **Google Cloud CLI** installed and authenticated
3. **Project access** to `wordbattle-secure`

### Basic Deployment

```bash
# Deploy to development environment
./deploy-unified.sh dev

# Deploy to testing environment  
./deploy-unified.sh testing

# Deploy to production environment
./deploy-unified.sh production
```

## Unified Deployment Script

### Script Usage

```bash
# Basic syntax
./deploy-unified.sh [environment] [git-branch] [options]

# Examples
./deploy-unified.sh dev                          # Deploy current branch to dev
./deploy-unified.sh testing feature/new-ui      # Deploy specific branch to testing
./deploy-unified.sh production --skip-git-check # Deploy to production without git validation
```

### Supported Environments

#### Development Environment (`dev`)
- **Service**: `wordbattle-backend-dev`
- **Config File**: `deploy.dev.env`
- **Resources**: 2 CPU, 2GB RAM
- **Scaling**: 0-10 instances
- **Database**: `wordbattle_dev`
- **Features**: Debug enabled, relaxed validation

#### Testing Environment (`testing`)
- **Service**: `wordbattle-backend-test`
- **Config File**: `deploy.testing.env`
- **Resources**: 1 CPU, 1GB RAM
- **Scaling**: 0-10 instances
- **Database**: `wordbattle_test`
- **Features**: Debug enabled, relaxed validation

#### Production Environment (`production`)
- **Service**: `wordbattle-backend-prod`
- **Config File**: `deploy.production.env`
- **Resources**: 2 CPU, 2GB RAM
- **Scaling**: 1-100 instances (always-on)
- **Database**: `wordbattle_prod`
- **Features**: Optimized for performance, strict validation

### Script Features

The deployment script automatically handles:

✅ **Environment Validation**: Validates required environment variables
✅ **Git Integration**: Checks for uncommitted changes (production only)
✅ **Docker Building**: Builds and tags images with environment-specific tags
✅ **Container Registry**: Pushes images to Google Container Registry
✅ **Cloud Run Deployment**: Deploys with proper configuration
✅ **Health Checks**: Tests deployment after completion
✅ **Contract Validation**: Validates API contracts (if available)
✅ **Cleanup**: Removes temporary build artifacts

## Environment Configuration Files

Each environment uses a dedicated configuration file:

### `deploy.dev.env`
```bash
# Development Environment Configuration
ENVIRONMENT=testing
PROJECT_ID=wordbattle-secure
GOOGLE_CLOUD_PROJECT=wordbattle-secure

# Database Configuration
DB_NAME=wordbattle_dev
DB_USER=wordbattle
DB_PASSWORD=p2n1kqcYFLbx51nsbhUkMYzAHz8oWUGOfwvK3H+okVI=

# Cloud SQL Configuration
CLOUD_SQL_INSTANCE_NAME=wordbattle-db
CLOUD_REGION=europe-west1
CLOUD_SQL_CONNECTION_NAME=wordbattle-secure:europe-west1:wordbattle-db

# SMTP Configuration (TLS on port 587)
SMTP_USERNAME=service@binge-wordbattle.de
SMTP_PASSWORD=z1nUNGrz1ZDmu4J
FROM_EMAIL=service@binge-wordbattle.de
SMTP_SERVER=smtp.strato.de
SMTP_PORT=587
SMTP_USE_SSL=false

# Security
SECRET_KEY=09a7f7fbd3bc514c5f51365b58c8055fc00261961ecfe048292dbf81ebcfe44f
ADMIN_EMAIL=jan@binge.de
```

### `deploy.testing.env`
Similar to dev but with `DB_NAME=wordbattle_test` and potentially different resources.

### `deploy.production.env`
Production configuration with `DB_NAME=wordbattle_prod` and production-optimized settings.

## Required Environment Variables

### Core Variables (All Environments)

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment identifier | `testing`, `production` |
| `PROJECT_ID` | Google Cloud Project ID | `wordbattle-secure` |
| `DB_NAME` | Target database name | `wordbattle_dev`, `wordbattle_prod` |
| `DB_USER` | Database user | `wordbattle` |
| `DB_PASSWORD` | Database password | (from Secret Manager) |
| `SECRET_KEY` | Application secret key | (secure random string) |
| `ADMIN_EMAIL` | Administrator email | `jan@binge.de` |

### SMTP Configuration (Required for Email)

| Variable | Value | Description |
|----------|-------|-------------|
| `SMTP_USERNAME` | `service@binge-wordbattle.de` | SMTP login |
| `SMTP_PASSWORD` | (from Secret Manager) | SMTP password |
| `FROM_EMAIL` | `service@binge-wordbattle.de` | Sender address |
| `SMTP_SERVER` | `smtp.strato.de` | SMTP server |
| `SMTP_PORT` | `587` | SMTP port (TLS) |
| `SMTP_USE_SSL` | `false` | Use TLS, not SSL |

### Cloud SQL Configuration

| Variable | Value |
|----------|-------|
| `CLOUD_SQL_INSTANCE_NAME` | `wordbattle-db` |
| `CLOUD_REGION` | `europe-west1` |
| `CLOUD_SQL_CONNECTION_NAME` | `wordbattle-secure:europe-west1:wordbattle-db` |

## Secret Manager Setup

The deployment script uses environment variables from the config files. For production deployments, consider using Secret Manager:

```bash
# Create secrets (if needed)
echo "your-db-password" | gcloud secrets create prod-db-password --data-file=- --project=wordbattle-secure
echo "your-smtp-password" | gcloud secrets create dev-smtp-password --data-file=- --project=wordbattle-secure

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding prod-db-password \
  --member="serviceAccount:15814336315-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=wordbattle-secure
```

## Deployment Process

### 1. Pre-deployment Validation

The script validates:
- Environment file exists and contains required variables
- Git repository state (production only)
- Docker and gcloud CLI availability
- Google Cloud project access

### 2. Build Process

```bash
# Automatic steps performed by script:
# 1. Load environment configuration
# 2. Validate prerequisites
# 3. Build Docker image with environment-specific tag
# 4. Push to Google Container Registry
# 5. Deploy to Cloud Run with proper configuration
```

### 3. Post-deployment Testing

The script automatically tests:
- Health endpoint (`/health`)
- API documentation (`/docs`)
- Contract validation (if available)

## Current Environment Status

### Production Environment (`wordbattle-backend-prod`)
- **Status**: ✅ Fully configured and healthy
- **Database**: `wordbattle_prod`
- **URL**: `https://wordbattle-backend-prod-15814336315.europe-west1.run.app`
- **Resources**: 2 CPU, 2GB RAM, 1-100 instances

### Development Environment (`wordbattle-backend-dev`)
- **Status**: ✅ Recently deployed with unified script
- **Database**: `wordbattle_dev` (contains production data copy)
- **URL**: `https://wordbattle-backend-dev-idgnvgsvva-ew.a.run.app`
- **Resources**: 2 CPU, 2GB RAM, 0-10 instances
- **Features**: Full production data for realistic testing

### Testing Environment (`wordbattle-backend-test`)
- **Status**: ⚠️ Available but use dev environment for most testing
- **Database**: `wordbattle_test`
- **Resources**: 1 CPU, 1GB RAM, 0-10 instances

## Troubleshooting

### Common Issues

**1. Deployment fails with "Environment file not found"**
```bash
# Solution: Create the required environment file
cp deploy.testing.env deploy.dev.env
# Edit deploy.dev.env with correct values
```

**2. Database connection fails**
```bash
# Check if Cloud SQL instance is running
gcloud sql instances describe wordbattle-db --project=wordbattle-secure

# Verify environment variables in deployed service
gcloud run services describe wordbattle-backend-dev --region=europe-west1 --project=wordbattle-secure
```

**3. SMTP errors in logs**
```bash
# Check SMTP configuration
curl -s https://your-service-url/health | jq .

# Verify SMTP settings in environment file
cat deploy.dev.env | grep SMTP
```

**4. Build fails with Docker errors**
```bash
# Ensure Docker is running
docker ps

# Check available disk space
df -h
```

### Debugging Commands

```bash
# View deployment logs
gcloud run services logs tail wordbattle-backend-dev --region=europe-west1 --project=wordbattle-secure

# Check service configuration
gcloud run services describe wordbattle-backend-dev --region=europe-west1 --project=wordbattle-secure

# Test health endpoint
curl -s https://your-service-url/health | jq .

# Check database status
curl -s https://your-service-url/database/status | jq .
```

## Best Practices

### Development Workflow

1. **Use dev environment** for feature development
2. **Test in testing environment** before production
3. **Always use the deployment script** for consistency
4. **Validate health checks** after deployment

### Environment Management

1. **Keep environment files secure** (they contain credentials)
2. **Use different databases** for each environment
3. **Test with realistic data** (copy production to dev as needed)
4. **Monitor resource usage** and adjust scaling as needed

### Git Integration

- **Production deployments** require clean git state
- **Development/testing** allows uncommitted changes
- **Git tags** are automatically created for production deployments

## Data Management

### Copying Production Data to Development

The development environment contains a complete copy of production data for realistic testing. To refresh this data:

```bash
# Use the copy script (if available)
python scripts/copy-prod-to-dev.py

# Or manual process:
# 1. Export production data
# 2. Clean development database
# 3. Import production data
# 4. Verify data integrity
```

This ensures development testing uses realistic data while keeping environments properly isolated.

## Migration Guide

### From Manual Deployment to Unified Script

1. **Delete manually created services** (if any)
2. **Create environment configuration file**
3. **Run deployment script**: `./deploy-unified.sh dev`
4. **Verify deployment** with health checks

The unified script ensures consistent, reliable deployments across all environments with proper configuration management.