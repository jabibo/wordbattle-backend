# WordBattle Backend Deployment Configuration

This document outlines the complete environment variable and secret configuration required for deploying the WordBattle backend to different environments.

## Environment Overview

The WordBattle backend supports multiple deployment environments:
- **Production**: `wordbattle-backend-prod` (project: `wordbattle-secure`)
- **Development**: `wordbattle-backend-dev` (project: `wordbattle-secure`)
- **Testing**: `wordbattle-backend-test` (project: `wordbattle-1748668162` - DEPRECATED)

## Required Environment Variables

### Database Configuration

All environments require these database-related variables:

| Variable | Production | Development | Description |
|----------|------------|-------------|-------------|
| `DB_NAME` | `wordbattle_prod` | `wordbattle_dev` | Target database name |
| `DB_USER` | `wordbattle` | `wordbattle` | Database user account |
| `GOOGLE_CLOUD_PROJECT` | `wordbattle-secure` | `wordbattle-secure` | GCP project ID |
| `CLOUD_SQL_CONNECTION_NAME` | `wordbattle-secure:europe-west1:wordbattle-db` | `wordbattle-secure:europe-west1:wordbattle-db` | Cloud SQL connection |

**Important**: Do NOT set `DB_HOST` or `DATABASE_URL` as environment variables. The app uses Cloud SQL connector with unix sockets.

### SMTP Configuration

All environments require these SMTP variables for email functionality:

| Variable | Value | Description |
|----------|-------|-------------|
| `SMTP_USERNAME` | `service@binge-wordbattle.de` | SMTP login username |
| `FROM_EMAIL` | `service@binge-wordbattle.de` | Email sender address |
| `SMTP_SERVER` | `smtp.strato.de` | SMTP server (has default) |
| `SMTP_PORT` | `465` | SMTP port (has default) |
| `SMTP_USE_SSL` | `true` | Use SSL (has default) |

### Secret Manager References

These values must be stored in Google Cloud Secret Manager and referenced as secrets:

| Secret Name | Used By | Description |
|-------------|---------|-------------|
| `prod-db-password` | Production & Dev | Database password for `wordbattle` user |
| `prod-smtp-password` | Production | SMTP password for email service |
| `dev-smtp-password` | Development | SMTP password for email service (same value as prod) |

## Current Environment Status

### Production Environment (`wordbattle-backend-prod`)
- **Status**: ✅ Fully configured and healthy
- **Database**: `wordbattle_prod` 
- **SMTP**: Configured with `prod-smtp-password` secret
- **URL**: `https://wordbattle-backend-prod-15814336315.europe-west1.run.app`

### Development Environment (`wordbattle-backend-dev`)
- **Status**: ✅ Recently configured with forfeit fixes and production data
- **Database**: `wordbattle_dev` (copied from production)
- **SMTP**: Configured with `dev-smtp-password` secret
- **URL**: `https://wordbattle-backend-dev-15814336315.europe-west1.run.app`
- **Data**: Complete copy of production database for testing

### Testing Environment (`wordbattle-backend-test`)
- **Status**: ❌ DEPRECATED - Project `wordbattle-1748668162` is deprecated
- **Recommendation**: Use development environment for testing instead

## Deployment Commands

### Using the Unified Deployment Script

The recommended way to deploy is using the unified deployment script:

```bash
# Deploy to production
./deploy-unified.sh production

# Deploy to development (not currently supported by script)
# Use manual Cloud Run deployment for development
```

### Manual Cloud Run Deployment

For development or manual deployments:

```bash
# Build and deploy to development
gcloud builds submit --tag europe-west1-docker.pkg.dev/wordbattle-secure/cloud-run-source-deploy/wordbattle-backend-dev:latest --project=wordbattle-secure

gcloud run deploy wordbattle-backend-dev \
  --image europe-west1-docker.pkg.dev/wordbattle-secure/cloud-run-source-deploy/wordbattle-backend-dev:latest \
  --region=europe-west1 \
  --project=wordbattle-secure \
  --set-env-vars="DB_NAME=wordbattle_dev,GOOGLE_CLOUD_PROJECT=wordbattle-secure,CLOUD_SQL_CONNECTION_NAME=wordbattle-secure:europe-west1:wordbattle-db,SMTP_USERNAME=service@binge-wordbattle.de,FROM_EMAIL=service@binge-wordbattle.de" \
  --update-secrets="DB_PASSWORD=prod-db-password:latest,SMTP_PASSWORD=dev-smtp-password:latest"
```

### Required Secret Manager Setup

Before deployment, ensure these secrets exist:

```bash
# Create database password secret (if not exists)
echo "HKrzBR4nMpF4ddgf" | gcloud secrets create prod-db-password --data-file=- --project=wordbattle-secure

# Create SMTP password secret (if not exists)  
echo "z1nUNGrz1ZDmu4J" | gcloud secrets create dev-smtp-password --data-file=- --project=wordbattle-secure

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding prod-db-password \
  --member="serviceAccount:15814336315-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=wordbattle-secure
```

## Troubleshooting Common Issues

### Database Connection Issues

**Symptom**: `Database unhealthy` in health check
**Solutions**:
1. Verify `DB_NAME` environment variable is set correctly
2. Check `GOOGLE_CLOUD_PROJECT` matches the Cloud SQL project
3. Ensure `CLOUD_SQL_CONNECTION_NAME` is correct
4. Verify Cloud SQL instance is running: `gcloud sql instances describe wordbattle-db --project=wordbattle-secure`

### Email Not Working

**Symptom**: SMTP errors or "email functionality disabled" in logs
**Solutions**:
1. Verify all SMTP environment variables are set: `SMTP_USERNAME`, `FROM_EMAIL`
2. Check SMTP password secret exists and is accessible
3. Ensure service account has Secret Manager access
4. Test with logs: Look for "SMTP_USERNAME not set" warnings

### Import Errors (Wrong Module References)

**Symptom**: `ModuleNotFoundError: No module named 'app.utils.auth'`
**Solution**: This is a known issue. The function is in `app.auth`, not `app.utils.auth`

## Environment Variable Checklist

Before considering a deployment complete, verify:

### ✅ Database Variables
- [ ] `DB_NAME` is set to correct database
- [ ] `GOOGLE_CLOUD_PROJECT` matches Cloud SQL project  
- [ ] `CLOUD_SQL_CONNECTION_NAME` is correct
- [ ] `DB_PASSWORD` secret is configured
- [ ] No `DB_HOST` or `DATABASE_URL` env vars (conflicts with Cloud SQL connector)

### ✅ SMTP Variables
- [ ] `SMTP_USERNAME=service@binge-wordbattle.de`
- [ ] `FROM_EMAIL=service@binge-wordbattle.de`
- [ ] `SMTP_PASSWORD` secret is configured
- [ ] Service account has Secret Manager access

### ✅ Health Checks
- [ ] `/health` endpoint returns "healthy"
- [ ] `/database/status` shows tables and data
- [ ] No error messages in Cloud Run logs

## Key Points to Remember

1. **Always use Secret Manager** for passwords, never hardcode them
2. **Database name differs by environment**: `wordbattle_prod` vs `wordbattle_dev`
3. **Don't set DB_HOST** - let Cloud SQL connector handle connections
4. **SMTP configuration is required** for email invitations and auth codes
5. **Service account needs Secret Manager access** for both DB and SMTP passwords
6. **Testing environment is deprecated** - use development environment instead

## Data Management

### Copying Production Data to Development

To copy production database to development for testing:

```bash
# Create temporary bucket
gsutil mb gs://wordbattle-db-copy-$(date +%s)

# Export production database
gcloud sql export sql wordbattle-db gs://bucket-name/prod-data.sql --database=wordbattle_prod --project=wordbattle-secure

# Clean development database (optional)
# Create and run cleanup SQL script if needed

# Import to development
gcloud sql import sql wordbattle-db gs://bucket-name/prod-data.sql --database=wordbattle_dev --project=wordbattle-secure

# Cleanup
gsutil rm -r gs://bucket-name/
```

This ensures development environment has realistic data for testing features like forfeit functionality.
