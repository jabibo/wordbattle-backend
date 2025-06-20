# 📁 Project Organization Guide

## Overview

The WordBattle backend project has been systematically organized to improve maintainability, developer onboarding, and clear separation of concerns. This document explains the new structure and how to navigate it effectively.

## 📚 Documentation Structure

### `/docs/` - Documentation Hub

The central documentation directory is organized into specialized subdirectories:

#### 📋 `/docs/current-features/`
Active system features and their documentation:
- `COMPUTER_PLAYER_AUTO_RECREATION.md` - Computer player management system
- Future feature documentation goes here

#### 🏗️ `/docs/deployment/`
Deployment guides and operational workflows:
- `DEPLOYMENT_GUIDE.md` - Comprehensive deployment instructions
- `DEVELOPMENT_WORKFLOW.md` - Git workflow and environment management
- `DEPLOYMENT_SAFETY.md` - Best practices and safety measures
- `README_DEPLOYMENT.md` - Legacy deployment documentation

#### 🔧 `/docs/troubleshooting/`
Problem resolution and debugging guides:
- `WEBSOCKET_TIMEOUT_FIX.md` - WebSocket connection timeout resolution
- Future troubleshooting guides go here

#### 📚 `/docs/archived-features/`
Historical documentation for completed projects:
- `GCP_MIGRATION_SUMMARY.md` - Google Cloud Platform migration details
- `SECURITY_ASSESSMENT.md` - Security analysis and improvements
- `PROJECT_STATUS.md` - Historical project status reports
- `REFACTORING_SUMMARY.md` - Major refactoring documentation

#### 🎨 `/docs/frontend/`
Frontend integration documentation (existing):
- Flutter setup guides
- Authentication examples
- API integration guides

#### 📖 Core Documentation Files
- `ADMIN.md` - Administrative tasks and management
- `DATABASE.md` - Database operations and management
- `API_REFERENCE.md` - API endpoint documentation
- `ARCHITECTURE.md` - System architecture overview

## 🗃️ Archive Organization

### `/archive/` - Historical Artifacts

Preserved development artifacts organized by category:

#### 🔬 `/archive/analysis-scripts/`
Development debugging and analysis tools:
- `debug_german_computer.py` - German language AI debugging
- `investigate_german_ai.py` - AI behavior analysis
- `test_ai_game_cycle.py` - Game cycle testing
- `test_websocket_moves.py` - WebSocket move testing
- `test_email_delivery.py` - Email system testing
- `refactor_analysis.md` - Refactoring analysis documentation

#### ⚙️ `/archive/old-configs/`
Deprecated configuration files:
- `auth_schemas.json` - Legacy authentication schemas
- `deploy-production.sh` - Old deployment scripts
- `deploy-test.sh` - Legacy test deployment
- `env-vars-test.yaml` - Deprecated environment configuration
- `wordbattle_backend_api_documentation.md` - Empty legacy documentation

#### 🚀 `/archive/alternative-deployments/`
Scripts for other platforms (Fly.io, Railway, Render):
- Various deployment alternatives attempted during development

#### ☁️ `/archive/aws-deployment/`
Legacy AWS App Runner deployment files:
- Historical AWS deployment configurations

#### 📜 `/archive/old-deployment-scripts/`
Previous deployment attempts and scripts:
- Various deployment iterations and experiments

#### 🐳 `/archive/old-dockerfiles/`
Previous Docker configurations:
- Legacy Dockerfile versions

#### 📚 `/archive/old-documentation/`
Previous documentation versions:
- Superseded documentation files

#### 🧪 `/archive/test-scripts/`
Development testing scripts and database utilities:
- Various test utilities used during development

## 🏗️ Active Project Structure

### Core Application Code
```
app/
├── routers/          # API endpoints
├── models/           # Database models
├── schemas/          # Pydantic schemas
├── utils/            # Utility functions
├── game_logic/       # Game engine
└── middleware/       # Custom middleware
```

### Database & Migration
```
alembic/              # Database migrations
migrations/           # Additional migration scripts
```

### Testing
```
tests/                # Comprehensive test suite
pytest.ini           # Test configuration
```

### Data & Scripts
```
data/                 # Word lists and static data
scripts/              # Utility and maintenance scripts
```

### Configuration & Deployment
```
deploy-unified.sh     # Main deployment script
Dockerfile.cloudrun   # Docker configuration for GCP
requirements.txt      # Python dependencies
.gitignore           # Enhanced ignore patterns
```

## 🔍 Finding Documentation

### By Topic
- **Deployment Issues**: Check `/docs/deployment/` and `/docs/troubleshooting/`
- **Feature Implementation**: Look in `/docs/current-features/`
- **Historical Context**: Browse `/docs/archived-features/`
- **API Integration**: Reference `/docs/frontend/` and core docs

### By File Type
- **Setup Guides**: `/docs/deployment/`
- **Feature Specs**: `/docs/current-features/`
- **Problem Solutions**: `/docs/troubleshooting/`
- **Legacy Information**: `/docs/archived-features/` and `/archive/`

## 📝 Adding New Documentation

### For New Features
Place documentation in `/docs/current-features/` with descriptive filenames.

### For Deployment Changes
Update guides in `/docs/deployment/` or add new deployment documentation there.

### For Troubleshooting
Add resolution guides to `/docs/troubleshooting/` with clear problem descriptions.

### For Historical Projects
When projects are completed, move their documentation to `/docs/archived-features/`.

## 🧹 Maintenance Guidelines

### Regular Cleanup
1. **Archive Completed Features**: Move finished project docs to archived-features
2. **Clean Root Directory**: Keep root directory minimal and organized
3. **Update README**: Reflect any major organizational changes
4. **Review Archives**: Periodically review archived content for relevance

### File Naming Conventions
- Use `UPPERCASE_WITH_UNDERSCORES.md` for major documentation
- Use descriptive names that indicate the content purpose
- Group related documentation in appropriate subdirectories

### Git Hygiene
- Temporary files are automatically ignored via enhanced `.gitignore`
- Analysis scripts and debugging tools go to `archive/analysis-scripts/`
- Configuration experiments go to `archive/old-configs/`

## 🎯 Benefits of This Organization

### For Developers
- **Clear Navigation**: Easy to find relevant documentation
- **Reduced Clutter**: Clean root directory improves focus
- **Historical Context**: Preserved development artifacts for reference

### For New Team Members
- **Structured Onboarding**: Clear documentation hierarchy
- **Feature Discovery**: Easy identification of current vs. legacy features
- **Learning Path**: Progressive documentation from basics to advanced topics

### For Maintenance
- **Easier Updates**: Clear ownership of documentation sections
- **Better Planning**: Historical context for feature evolution
- **Quality Control**: Organized structure encourages documentation best practices

---

*This organization was implemented on June 20, 2025, as part of a comprehensive project cleanup initiative. For questions about this structure, refer to the git history or contact the development team.* 