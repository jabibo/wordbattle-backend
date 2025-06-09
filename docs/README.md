# WordBattle Backend Documentation

Welcome to the WordBattle Backend documentation. This directory contains comprehensive guides for development, deployment, and administration.

## 📋 Documentation Index

### 🚀 Deployment & Operations
- **[Deployment Workflow](DEPLOYMENT_WORKFLOW.md)** - Complete deployment process and git workflow
- **[Branch-Based Workflow](BRANCH_WORKFLOW.md)** - Alternative branch-based deployment strategy
- **[Deployment Scripts](DEPLOYMENT_SCRIPTS.md)** - Quick reference for all deployment commands
- **[Database Setup](DATABASE_SETUP.md)** - Database configuration and troubleshooting
- **[Admin Endpoints](ADMIN_ENDPOINTS.md)** - Administrative API endpoints and usage

### 🔧 Quick Start

#### First Time Setup
```bash
# Clone and setup
git clone https://github.com/jabibo/wordbattle-backend.git
cd wordbattle-backend

# Deploy to test environment
./deploy-test.sh

# Create default admin user
curl -X POST "https://your-test-url.com/admin/database/create-default-admin"
```

#### Development Workflow
```bash
# 1. Make changes
git add .
git commit -m "Your changes"
git push origin main

# 2. Test deployment
./deploy-test.sh

# 3. Production deployment (when ready)
./deploy-production.sh
```

## 🌿 Branch-Based Development (Optional)

If you prefer feature branches:

```bash
# Create feature branch
git checkout -b feature/new-feature

# Deploy feature to test
./deploy-test.sh feature/new-feature

# Merge when ready
git checkout main
git merge feature/new-feature
./deploy-production.sh
```

## 🏗️ Architecture Overview

### Environments
- **Production**: `wordbattle-backend-prod` → `wordbattle_db` database
- **Test**: `wordbattle-backend-test` → `wordbattle_test` database

### Key Components
- **FastAPI Backend** - Python web framework
- **PostgreSQL Database** - Cloud SQL instance
- **Google Cloud Run** - Serverless deployment
- **SMTP Email** - User authentication via email codes

### Admin System
- **Default Admin**: `jan@binge.de` (password: `admin123!WordBattle`)
- **Admin Endpoints**: Database management, user administration
- **Reset Functionality**: Safe game resets with admin preservation

## 📊 Monitoring & Health Checks

### Production Health
```bash
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/health
```

### Admin Status
```bash
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/admin/database/admin-status
```

### Wordlist Status
```bash
curl https://wordbattle-backend-prod-441752988736.europe-west1.run.app/admin/database/wordlist-status
```

## 🗄️ Database Management

### Import Wordlists
```bash
curl -X POST "https://your-domain.com/admin/database/import-wordlists"
```

### Reset Game Data (Safe)
```bash
curl -X POST "https://your-domain.com/admin/database/reset-games" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Create Admin User
```bash
curl -X POST "https://your-domain.com/admin/database/create-default-admin"
```

## 🔐 Security & Authentication

### Admin Authentication
- Controlled by `users.is_admin` and `users.is_word_admin` database fields
- Default admin user created automatically during resets
- All admin actions are logged with user information

### Environment Security
- Secrets generated per deployment
- Database credentials managed via environment variables
- CORS configured for mobile app access

## 🆘 Troubleshooting

### Common Issues

**Deployment fails with uncommitted changes:**
```bash
git add .
git commit -m "Your changes"
git push origin main
./deploy-production.sh
```

**Database connection issues:**
- Check Cloud SQL instance status
- Verify database credentials in deployment scripts
- Check environment variables

**Admin access issues:**
```bash
# Create admin user
curl -X POST "https://your-domain.com/admin/database/create-default-admin"

# Check admin status  
curl "https://your-domain.com/admin/database/admin-status"
```

## 📚 Additional Resources

### API Documentation
- **Production**: https://wordbattle-backend-prod-441752988736.europe-west1.run.app/docs
- **Test**: https://wordbattle-backend-test-441752988736.europe-west1.run.app/docs

### Git Repository
- **Main Repository**: https://github.com/jabibo/wordbattle-backend
- **Deployment Tags**: View with `git tag | grep deploy-prod`

### Cloud Resources
- **Google Cloud Console**: https://console.cloud.google.com/
- **Cloud Run Services**: https://console.cloud.google.com/run
- **Cloud SQL**: https://console.cloud.google.com/sql

---

## 📝 Contributing

1. Read the [Deployment Workflow](DEPLOYMENT_WORKFLOW.md) documentation
2. Follow the git workflow for your changes
3. Test in the test environment before production deployment
4. Update documentation when adding new features

For questions or issues, check the troubleshooting section above or refer to the specific documentation files. 