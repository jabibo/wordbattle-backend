# Archive Directory

This directory contains historical files and deprecated code from the WordBattle backend development process. These files are preserved for reference and debugging purposes but are **not part of the current production system**.

## 📁 Directory Structure

### `aws-deployment/`
Legacy AWS deployment files when the project was hosted on AWS App Runner:
- PowerShell and Bash scripts for AWS deployment
- IAM role configuration files
- App Runner service management scripts
- AWS-specific debugging tools

**Status**: ❌ Deprecated (migrated to GCP in December 2024)

### `old-deployment-scripts/`
Various deployment attempts and experimental scripts:
- Multiple iterations of GCP deployment scripts
- Alternative cloud provider scripts (Fly.io, Railway, Render)
- Shell scripts for monitoring and status checking
- Legacy working versions and extracted code directories
- Python deployment automation scripts

**Status**: ❌ Replaced by `deploy-gcp-production.ps1` and `deploy-gcp-production.sh`

### `test-scripts/`
Development and testing utilities:
- Database testing and validation scripts
- User creation and management scripts
- Game flow testing scripts
- Endpoint testing tools
- Migration and seeding scripts
- Database reset utilities

**Status**: ⚠️ Reference only (some functionality moved to proper test suite)

### `old-dockerfiles/`
Previous Docker configurations:
- `Dockerfile.prod` - Production Docker setup (pre-GCP)
- `Dockerfile.test` - Testing environment setup
- `Dockerfile.patch` - Temporary fixes

**Status**: ❌ Replaced by `Dockerfile.cloudrun`

### `old-configs/`
Outdated configuration files:
- Various `update-*.json` configuration files
- Docker Compose files for testing and SQLite
- Service update configurations

**Status**: ❌ Superseded by current environment-based configuration

### `alternative-deployments/`
Scripts for various cloud platforms that were tested:
- `deploy-fly.sh` - Fly.io deployment
- `deploy-railway.sh` - Railway deployment  
- `deploy-render.sh` - Render deployment
- Various GCP deployment iterations

**Status**: ❌ Not used (standardized on GCP Cloud Run)

### `old-documentation/`
Previous documentation versions:
- AWS-specific deployment guides
- Multiple migration summaries
- Production readiness documentation
- Internationalization implementation notes
- Game testing rules and procedures

**Status**: ❌ Replaced by current documentation

## 🔍 Why These Files Are Archived

1. **Historical Reference**: Complete audit trail of the project's evolution
2. **Debugging**: Ability to reference previous implementations if issues arise
3. **Learning**: Examples of different deployment approaches and configurations
4. **Recovery**: Backup of working configurations from different development phases

## ⚠️ Important Notes

- **DO NOT** use any files from this archive in production
- These files may contain outdated dependencies or security vulnerabilities
- Configuration files may reference old API endpoints or credentials
- Test scripts may be incompatible with the current database schema

## 🎯 Current Production System

For the current, supported deployment and configuration:
- Use `deploy-gcp-production.ps1` or `deploy-gcp-production.sh`
- Reference `DEPLOYMENT_GUIDE.md` and `GCP_MIGRATION_SUMMARY.md`
- Use `Dockerfile.cloudrun` for containerization
- Follow the main `README.md` for setup instructions

## 📅 Archive Timeline

- **Pre-December 2024**: AWS App Runner deployment era
- **December 2024**: GCP migration and cleanup
- **Current**: Clean, production-ready GCP deployment with Git integration

---

*This archive represents the journey from experimental deployment scripts to a professional, Git-integrated deployment pipeline on Google Cloud Platform.* 