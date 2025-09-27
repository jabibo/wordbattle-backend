# 🚀 WordBattle Backend Deployment Guide

This guide provides step-by-step instructions for deploying the WordBattle backend to Google Cloud Platform using the unified deployment script.

## 📋 Prerequisites

Before deploying, ensure you have:

- **Google Cloud Account** with appropriate permissions
- **Google Cloud CLI** installed and authenticated (`gcloud auth login`)
- **Docker** installed and running
- **Git** for version control
- **Access to project**: `wordbattle-secure`

## 🎯 Quick Start (Recommended)

The fastest way to deploy is using our unified deployment script:

```bash
# Navigate to backend directory
cd wordbattle-backend

# Deploy to development environment
./deploy-unified.sh dev

# Deploy to production environment
./deploy-unified.sh production
```

### Complete Deployment Workflow

For a full deployment across backend and frontend:

```bash
# 1. Deploy backend
cd wordbattle-backend
./deploy-unified.sh production

# 2. Switch frontend environment
cd ../wordbattle-frontend
./scripts/switch_environment.sh production

# 3. Deploy to TestFlight (iOS)
./scripts/deploy_production_automated.sh
```

### Frontend Environment Switching

The frontend environment switch script automatically updates configuration files:

```bash
# Navigate to frontend directory
cd wordbattle-frontend

# Switch frontend to development backend
./scripts/switch_environment.sh dev

# Switch frontend to production backend  
./scripts/switch_environment.sh production
```

**What the script does:**
- ✅ Updates `currentEnvironment` setting
- ✅ Configures backend API and WebSocket URLs
- ✅ Sets development features (debug mode, logging)
- ✅ Creates automatic backup of previous configuration
- ✅ Validates changes and provides verification

The script handles everything automatically:
- ✅ Environment validation
- ✅ Docker image building and pushing
- ✅ Cloud Run service deployment
- ✅ Health checks and validation
- ✅ Git integration and tagging

## 🚀 Unified Deployment Script

### Basic Usage

```bash
# Syntax
./deploy-unified.sh [environment] [git-branch] [options]

# Examples
./deploy-unified.sh dev                          # Deploy current branch to dev
./deploy-unified.sh production                   # Deploy to production
./deploy-unified.sh production main              # Deploy specific branch to production
./deploy-unified.sh production --skip-git-check  # Deploy to production without git validation
```

### Supported Environments

#### 🛠️ Development Environment (`dev`)
```bash
./deploy-unified.sh dev
```

- **Service**: `wordbattle-backend-dev`
- **URL**: `https://wordbattle-backend-dev-15814336315.europe-west1.run.app`
- **Database**: `wordbattle_dev` (contains production data copy)
- **Resources**: 2 CPU, 2GB RAM
- **Scaling**: 0-10 instances (scales to zero when idle)
- **Features**: Debug enabled, realistic test data, SMTP configured

#### 🏭 Production Environment (`production`)
```bash
./deploy-unified.sh production
```

- **Service**: `wordbattle-backend-prod`
- **URL**: `https://wordbattle-backend-prod-15814336315.europe-west1.run.app`
- **Database**: `wordbattle_prod`
- **Resources**: 2 CPU, 2GB RAM
- **Scaling**: 1-100 instances (always-on)
- **Features**: Optimized for performance, strict validation, Git tagging

### Script Features

The deployment script automatically handles:

✅ **Environment Validation**: Checks required variables and configuration
✅ **Git Integration**: Validates git state, creates tags for production
✅ **Docker Building**: Builds optimized images with environment-specific tags
✅ **Container Registry**: Pushes to Google Container Registry (GCR)
✅ **Cloud Run Deployment**: Deploys with proper configuration and scaling
✅ **Health Checks**: Tests endpoints after deployment
✅ **Contract Validation**: Validates API contracts (if available)
✅ **Cleanup**: Removes temporary build artifacts

## 📁 Environment Configuration

Each environment uses a dedicated configuration file in the backend directory:

### `deploy.dev.env` (Development)
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

### `deploy.testing.env` (Testing)
Similar configuration with `DB_NAME=wordbattle_test` and testing-specific settings.

### `deploy.production.env` (Production)
Production configuration with `DB_NAME=wordbattle_prod` and production-optimized settings.

## 🛠️ Manual Deployment (Advanced)

For advanced users or custom deployments:

### Step 1: Build Docker Image

```bash
# Navigate to backend directory
cd wordbattle-backend

# Build image
gcloud builds submit --tag gcr.io/wordbattle-secure/wordbattle-backend:latest --project=wordbattle-secure
```

### Step 2: Deploy to Cloud Run

```bash
# Deploy with environment variables
gcloud run deploy wordbattle-backend-dev \
  --image gcr.io/wordbattle-secure/wordbattle-backend:latest \
  --region=europe-west1 \
  --project=wordbattle-secure \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --set-env-vars="DB_NAME=wordbattle_dev,GOOGLE_CLOUD_PROJECT=wordbattle-secure" \
  --add-cloudsql-instances=wordbattle-secure:europe-west1:wordbattle-db
```

## 🔐 Security Configuration

### Required Environment Variables

| Category | Variable | Description | Example |
|----------|----------|-------------|---------|
| **Core** | `PROJECT_ID` | Google Cloud Project ID | `wordbattle-secure` |
| | `ENVIRONMENT` | Environment identifier | `testing`, `production` |
| | `SECRET_KEY` | Application secret key | (64-char random string) |
| **Database** | `DB_NAME` | Target database name | `wordbattle_dev` |
| | `DB_USER` | Database user | `wordbattle` |
| | `DB_PASSWORD` | Database password | (from Secret Manager) |
| | `CLOUD_SQL_CONNECTION_NAME` | Cloud SQL connection | `wordbattle-secure:europe-west1:wordbattle-db` |
| **Email** | `SMTP_USERNAME` | SMTP login | `service@binge-wordbattle.de` |
| | `SMTP_PASSWORD` | SMTP password | (secure password) |
| | `FROM_EMAIL` | Sender email | `service@binge-wordbattle.de` |
| | `SMTP_SERVER` | SMTP server | `smtp.strato.de` |
| | `SMTP_PORT` | SMTP port | `587` (TLS) |
| | `SMTP_USE_SSL` | Use SSL/TLS | `false` (use TLS) |

### Secret Manager Setup

For production deployments, use Google Cloud Secret Manager:

```bash
# Create database password secret
echo "your-secure-password" | gcloud secrets create prod-db-password --data-file=- --project=wordbattle-secure

# Create SMTP password secret
echo "your-smtp-password" | gcloud secrets create dev-smtp-password --data-file=- --project=wordbattle-secure

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding prod-db-password \
  --member="serviceAccount:15814336315-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=wordbattle-secure
```

### Database Security

1. **Cloud SQL Connector**: Uses unix sockets for secure connections
2. **Private IP**: Database uses private networking
3. **SSL Encryption**: All connections encrypted in transit
4. **IAM Authentication**: Service accounts for access control

## 📊 Monitoring and Health Checks

### Built-in Health Endpoints

```bash
# Health check
curl https://your-service-url/health

# Database status
curl https://your-service-url/database/status

# API documentation
curl https://your-service-url/docs
```

### Cloud Logging

View deployment and runtime logs:

```bash
# View deployment logs
gcloud run services logs tail wordbattle-backend-dev --region=europe-west1 --project=wordbattle-secure

# Filter for errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wordbattle-backend-dev AND severity>=ERROR" --project=wordbattle-secure --limit=10
```

### Cloud Monitoring

The deployment automatically sets up:
- **Application logs**: Structured logging to Cloud Logging
- **Health checks**: Automatic monitoring of `/health` endpoint  
- **Metrics**: CPU, memory, and request metrics
- **Alerts**: Can be configured for critical metrics

## 🔄 Deployment Strategies

### Development Workflow

1. **Feature Development**: Use `dev` environment
   ```bash
   ./deploy-unified.sh dev
   ```

2. **Testing**: Deploy to `testing` environment
   ```bash
   ./deploy-unified.sh testing
   ```

3. **Production**: Deploy stable features
   ```bash
   ./deploy-unified.sh production
   ```

### Git Integration

- **Development/Testing**: Allows uncommitted changes
- **Production**: Requires clean git state
- **Automatic Tagging**: Production deployments create git tags
- **Branch Deployment**: Can deploy specific branches to testing

### Blue-Green Deployment

Cloud Run automatically handles blue-green deployments:
- New revisions are created for each deployment
- Traffic gradually shifts to new revision
- Old revisions remain available for rollback

## 🚨 Troubleshooting

### Common Issues

#### 1. Environment File Not Found
```bash
# Error: Environment file deploy.dev.env not found
# Solution: Create environment file
cp deploy.testing.env deploy.dev.env
# Edit deploy.dev.env with correct values
```

#### 2. Database Connection Failed
```bash
# Check Cloud SQL instance status
gcloud sql instances describe wordbattle-db --project=wordbattle-secure

# Check if instance is stopped
gcloud sql instances patch wordbattle-db --activation-policy=ALWAYS --project=wordbattle-secure
```

#### 3. Docker Build Failed
```bash
# Ensure Docker is running
docker ps

# Check disk space
df -h

# Clear Docker cache if needed
docker system prune -f
```

#### 4. Permission Denied Errors
```bash
# Re-authenticate with gcloud
gcloud auth login

# Set correct project
gcloud config set project wordbattle-secure

# Check IAM permissions
gcloud projects get-iam-policy wordbattle-secure
```

#### 5. SMTP Configuration Issues
```bash
# Check SMTP settings in environment file
cat deploy.dev.env | grep SMTP

# Test SMTP connectivity
curl -s https://your-service-url/health | jq .

# Check logs for SMTP errors
gcloud logging read "resource.labels.service_name=wordbattle-backend-dev AND textPayload:(SMTP OR email)" --project=wordbattle-secure --limit=5
```

### Debugging Commands

```bash
# Check service status
gcloud run services describe wordbattle-backend-dev --region=europe-west1 --project=wordbattle-secure

# View current configuration
gcloud run services describe wordbattle-backend-dev --region=europe-west1 --project=wordbattle-secure --format="yaml"

# Test health endpoint
curl -s https://your-service-url/health | jq .

# Check recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wordbattle-backend-dev" --project=wordbattle-secure --limit=10 --format="value(timestamp,textPayload)"
```

## 💰 Cost Optimization

### Development Environment
- **Auto-scaling**: Scales to 0 when not in use
- **Resource limits**: 2 CPU, 2GB RAM maximum
- **Storage**: Shared database with production data

### Testing Environment  
- **Minimal resources**: 1 CPU, 1GB RAM
- **Separate database**: Independent test data
- **Cost-effective**: Pay only when running

### Production Environment
- **Always-on**: Minimum 1 instance for availability
- **Performance**: Optimized resources for production load
- **Monitoring**: Enhanced logging and monitoring

### Cost Monitoring

Set up billing alerts:
```bash
# Create budget alert
gcloud billing budgets create \
  --billing-account=YOUR-BILLING-ACCOUNT \
  --display-name="WordBattle Backend Budget" \
  --budget-amount=100USD
```

## 🔄 Data Management

### Environment Data Strategy

- **Production**: Live user data (`wordbattle_prod`)
- **Development**: Copy of production data (`wordbattle_dev`) for realistic testing
- **Testing**: Minimal test data (`wordbattle_test`) for automated tests

### Data Refresh

Refresh development data from production:
```bash
# Use the copy script (if available)
python scripts/copy-prod-to-dev.py

# Or use the deployment script with fresh data
./deploy-unified.sh dev
```

## 📱 Frontend Deployment (TestFlight)

### iOS TestFlight Deployment

After deploying the backend, deploy the frontend to TestFlight:

```bash
# Navigate to frontend directory
cd wordbattle-frontend

# Ensure environment is set correctly
./scripts/switch_environment.sh production

# Deploy to TestFlight using automated script
./scripts/deploy_production_automated.sh
```

### Prerequisites for TestFlight

- **macOS** with Xcode installed
- **Apple Developer Account** with appropriate permissions
- **Environment file** (`.env`) with Apple credentials:
  ```bash
  APPLE_ID=your-apple-id@example.com
  APPLE_APP_SPECIFIC_PASSWORD=your-app-specific-password
  ```

### TestFlight Deployment Process

The automated script handles:
1. ✅ **Environment validation**: Checks Git status and credentials
2. ✅ **Dependency installation**: Updates Flutter packages and CocoaPods
3. ✅ **iOS archive building**: Creates optimized production build
4. ✅ **Direct upload**: Uploads directly to App Store Connect
5. ✅ **Processing verification**: Build appears in TestFlight within 10-15 minutes

### Frontend Environment Configuration

| Environment | Backend URL | Features |
|-------------|-------------|----------|
| Development | `wordbattle-backend-dev-*` | Debug enabled, development features |
| Production | `wordbattle-backend-prod-*` | Optimized performance, production ready |

Use the environment switch script to ensure frontend points to the correct backend before deployment.

## 📞 Support and Best Practices

### Best Practices

1. **Use the deployment script**: Ensures consistent deployments
2. **Test in dev first**: Always test changes in development
3. **Environment isolation**: Keep environments separate
4. **Monitor deployments**: Check health endpoints after deployment
5. **Keep credentials secure**: Use Secret Manager for sensitive data
6. **Frontend-backend alignment**: Use environment switch script before deploying frontend

### Getting Help

1. **Check troubleshooting section** above
2. **Review Cloud Run logs** for specific errors
3. **Consult Google Cloud documentation**
4. **Check environment configuration** files

## 🎉 Next Steps

After successful deployment:

1. **Configure monitoring**: Set up Cloud Monitoring alerts
2. **Custom domain**: Configure custom domain with Cloud DNS
3. **SSL certificates**: Managed SSL certificates are automatic
4. **CDN**: Consider Cloud CDN for static assets
5. **Security**: Implement Cloud Armor for additional protection
6. **Backup strategy**: Configure automated database backups

## 📋 Environment Checklist

After deployment, verify:

### ✅ Core Functionality
- [ ] Health endpoint returns "healthy"
- [ ] Database connection working
- [ ] API documentation accessible
- [ ] Authentication endpoints working

### ✅ Email Functionality  
- [ ] SMTP configuration correct
- [ ] Email sending working
- [ ] Verification codes being sent
- [ ] Invitation emails working

### ✅ Performance
- [ ] Response times acceptable
- [ ] Auto-scaling configured
- [ ] Resource limits appropriate
- [ ] Monitoring enabled

### ✅ Security
- [ ] HTTPS enabled (automatic)
- [ ] Database using private networking
- [ ] Secrets stored in Secret Manager
- [ ] IAM permissions configured

---

**Happy Deploying! 🚀**

For questions or issues, refer to the troubleshooting section or check the logs using the commands provided above.