# WordBattle Backend

A FastAPI-based backend for the WordBattle mobile game, deployed on Google Cloud Run with PostgreSQL database.

## 🚀 Quick Start

### Deploy to Test Environment
```bash
./deploy-test.sh
```

### Deploy to Production
```bash
./deploy-production.sh
```

### Create Admin User
```bash
curl -X POST "https://your-domain.com/admin/database/create-default-admin"
```

## 📚 Documentation

For comprehensive guides and documentation, see the **[docs/](docs/)** directory:

- **[📖 Documentation Index](docs/README.md)** - Complete documentation overview
- **[🚀 Deployment Workflow](docs/DEPLOYMENT_WORKFLOW.md)** - Git-based deployment process  
- **[🌿 Branch Workflow](docs/BRANCH_WORKFLOW.md)** - Feature branch deployment strategy
- **[👑 Admin Endpoints](docs/ADMIN_ENDPOINTS.md)** - Administrative API reference
- **[⚡ Deployment Scripts](docs/DEPLOYMENT_SCRIPTS.md)** - Quick script reference

## 🏗️ Architecture

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (Google Cloud SQL)
- **Deployment**: Google Cloud Run
- **Authentication**: Email-based with JWT tokens
- **Admin System**: Built-in administrative endpoints

## 🌐 Environments

- **Production**: `wordbattle-backend-prod` → `wordbattle_db`
- **Test**: `wordbattle-backend-test` → `wordbattle_test`

## 🔧 Development

### Standard Workflow
```bash
# 1. Make changes
git add .
git commit -m "Your changes"
git push origin main

# 2. Test
./deploy-test.sh

# 3. Production (when ready)
./deploy-production.sh
```

### Branch-Based Development
```bash
# Create and test feature branch
git checkout -b feature/new-feature
./deploy-test.sh feature/new-feature

# Merge when ready
git checkout main
git merge feature/new-feature
./deploy-production.sh
```

## 🔐 Admin Access

**Default Admin User**:
- Email: `jan@binge.de`
- Password: `admin123!WordBattle`
- Created automatically during database resets

## 📊 Health Checks

- **Production**: https://wordbattle-backend-prod-441752988736.europe-west1.run.app/health
- **Test**: https://wordbattle-backend-test-441752988736.europe-west1.run.app/health

## 🆘 Support

For detailed troubleshooting, workflow guides, and API documentation, visit the **[docs/](docs/)** directory.