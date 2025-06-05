# WordBattle Backend

[![Coverage](https://img.shields.io/badge/coverage-83%25-green.svg)](https://github.com/yourusername/wordbattle-backend)

A FastAPI backend for a multiplayer word game similar to Scrabble, deployed on Google Cloud Platform.

## 🚀 Current Deployment Status

**Production Environment**: Google Cloud Run  
**Current Branch**: `main`  
**Deployment**: Automated via Git-integrated pipeline  

The application is currently running on GCP with multi-environment support (production and testing).

## 📁 Project Structure

```
wordbattle-backend/
├── app/                    # Main application code
├── alembic/               # Database migrations
├── tests/                 # Test suite
├── terraform/             # GCP infrastructure as code
├── docs/                  # Documentation
├── data/                  # Static data files
├── migrations/            # Database migration scripts
├── scripts/               # Utility scripts
├── archive/              # Old/deprecated files
│   ├── aws-deployment/   # Legacy AWS deployment files
│   ├── old-deployment-scripts/
│   ├── test-scripts/
│   ├── old-dockerfiles/
│   ├── old-configs/
│   ├── alternative-deployments/
│   └── old-documentation/
├── deploy-gcp-production.ps1  # Main deployment script (PowerShell)
├── deploy-gcp-production.sh   # Main deployment script (Bash)
├── DEPLOYMENT_GUIDE.md        # Deployment instructions
├── GCP_MIGRATION_SUMMARY.md   # Migration details
└── Dockerfile.cloudrun        # Docker configuration for GCP
```

## 🔧 Quick Start

### Prerequisites
- Python 3.9+
- Docker
- Google Cloud SDK (for deployment)
- Git

### Local Development

1. **Clone and setup:**
```bash
git clone <repository-url>
cd wordbattle-backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment configuration:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Database setup:**
```bash
alembic upgrade head
```

4. **Run locally:**
```bash
uvicorn app.main:app --reload
```

API available at: http://localhost:8000

## 🌐 Deployment

### Production Deployment (GCP)

**PowerShell:**
```powershell
.\deploy-gcp-production.ps1 -Environment "production"
```

**Bash:**
```bash
./deploy-gcp-production.sh production
```

### Testing Environment

**PowerShell:**
```powershell
.\deploy-gcp-production.ps1 -Environment "testing"
```

**Bash:**
```bash
./deploy-gcp-production.sh testing
```

For detailed deployment instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

## 📖 Key Environment Variables

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration (default: 30)
- `DEFAULT_WORDLIST_PATH`: Path to wordlist file
- `LETTER_POOL_SIZE`: Letters per player rack (default: 7)
- `GAME_INACTIVE_DAYS`: Days before game abandonment (default: 7)

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app --cov-report=html
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Spec**: [wordbattle_backend_api_documentation.md](wordbattle_backend_api_documentation.md)

## 🗃️ Archive Directory

The `archive/` directory contains historical files from the development process:

- **aws-deployment/**: Legacy AWS App Runner deployment files
- **old-deployment-scripts/**: Previous deployment attempts and alternatives
- **test-scripts/**: Development testing scripts and database utilities
- **old-dockerfiles/**: Previous Docker configurations
- **old-configs/**: Outdated configuration files
- **alternative-deployments/**: Scripts for Fly.io, Railway, Render deployments
- **old-documentation/**: Previous documentation versions

These files are preserved for reference but are not part of the current production system.

## 🎮 Game Features

- **Multiplayer word placement** similar to Scrabble
- **Multi-language wordlist support** (German, English, etc.)
- **Real-time gameplay** via WebSocket connections
- **Invitation system** for private games
- **Score tracking** with letter and bonus calculations
- **Intelligent game ending** based on various conditions

## 🏗️ Infrastructure

- **Platform**: Google Cloud Platform
- **Compute**: Cloud Run (serverless containers)
- **Database**: Cloud SQL PostgreSQL
- **Container Registry**: Google Container Registry
- **Secrets**: Google Secret Manager
- **Infrastructure**: Terraform-managed

## 📄 License

MIT