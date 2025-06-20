# WordBattle Backend

[![Coverage](https://img.shields.io/badge/coverage-83%25-green.svg)](https://github.com/yourusername/wordbattle-backend)

A FastAPI backend for a multiplayer word game similar to Scrabble, deployed on Google Cloud Platform.

## 🚀 Current Deployment Status

**Production Environment**: Google Cloud Run  
**Current Branch**: `main`  
**Deployment**: Unified deployment pipeline via `deploy-unified.sh`  

The application is currently running on GCP with multi-environment support (production and testing).

## 📁 Project Structure

```
wordbattle-backend/
├── app/                          # Main application code
│   ├── routers/                  # API endpoints
│   ├── models/                   # Database models  
│   ├── schemas/                  # Pydantic schemas
│   ├── utils/                    # Utility functions
│   ├── game_logic/               # Game engine
│   └── middleware/               # Custom middleware
├── alembic/                      # Database migrations
├── tests/                        # Test suite
├── docs/                         # 📚 Documentation Hub
│   ├── current-features/         # Current system features
│   ├── archived-features/        # Completed project docs
│   ├── troubleshooting/          # Problem resolution guides
│   ├── deployment/               # Deployment guides
│   └── frontend/                 # Frontend integration docs
├── data/                         # Word lists and static data
├── scripts/                      # Utility and maintenance scripts
├── archive/                      # 🗃️ Historical files
│   ├── analysis-scripts/         # Development analysis tools
│   ├── aws-deployment/           # Legacy AWS deployment
│   ├── old-deployment-scripts/   # Previous deployment attempts
│   ├── old-configs/              # Deprecated configurations
│   └── alternative-deployments/ # Other platform deployments
├── deploy-unified.sh             # 🚀 Main deployment script
├── Dockerfile.cloudrun           # Docker configuration for GCP
└── requirements.txt              # Python dependencies
```

## 🔧 Quick Start

### Prerequisites
- Python 3.11+
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
cp deploy.testing.env.example deploy.testing.env
# Edit with your configuration
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

### Unified Deployment Script

The project uses a single, comprehensive deployment script for both environments:

**Testing Environment:**
```bash
./deploy-unified.sh testing
```

**Production Environment:**
```bash
./deploy-unified.sh production
```

The script automatically handles:
- ✅ Environment validation
- ✅ Git integration and tagging
- ✅ Docker image building and pushing
- ✅ Contract validation
- ✅ Health checks and verification
- ✅ Comprehensive testing

For detailed deployment instructions, see [docs/deployment/DEPLOYMENT_GUIDE.md](docs/deployment/DEPLOYMENT_GUIDE.md).

## 📖 Key Environment Variables

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key  
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration (default: 240 - 4 hours)
- `DEFAULT_WORDLIST_PATH`: Path to wordlist file
- `LETTER_POOL_SIZE`: Letters per player rack (default: 7)
- `GAME_INACTIVE_DAYS`: Days before game abandonment (default: 7)

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app --cov-report=html

# Run specific test categories
python -m pytest tests/test_auth.py
python -m pytest tests/test_game_logic.py
```

## 📚 Documentation

### 🔗 Quick Links
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:8000/redoc (ReDoc)

### 📖 Documentation Organization

#### Current System Documentation
- **[docs/current-features/](docs/current-features/)** - Active features and implementations
  - Computer Player Auto-Recreation
  - Authentication System
  - Game Logic

#### Deployment & Operations  
- **[docs/deployment/](docs/deployment/)** - Deployment guides and workflows
  - Deployment Guide - Comprehensive deployment instructions
  - Development Workflow - Git workflow and environment management
  - Deployment Safety - Best practices and safety measures

#### Troubleshooting & Support
- **[docs/troubleshooting/](docs/troubleshooting/)** - Problem resolution
  - WebSocket Timeout Fix
  - Common Issues and Solutions

#### Integration Documentation
- **[docs/frontend/](docs/frontend/)** - Frontend team integration guides
- **[docs/ADMIN.md](docs/ADMIN.md)** - Administrative tasks and management
- **[docs/DATABASE.md](docs/DATABASE.md)** - Database operations

#### Historical Documentation
- **[docs/archived-features/](docs/archived-features/)** - Completed projects and migrations
  - GCP Migration Summary
  - Security Assessment
  - Project Status Reports

## 🗃️ Archive Directory

The `archive/` directory preserves historical development artifacts:

- **analysis-scripts/**: Development debugging and analysis tools
- **aws-deployment/**: Legacy AWS App Runner deployment files  
- **old-deployment-scripts/**: Previous deployment attempts
- **old-configs/**: Deprecated configuration files
- **alternative-deployments/**: Scripts for other platforms (Fly.io, Railway, Render)

These files are preserved for reference but are not part of the current production system.

## 🎮 Game Features

- **Multiplayer word placement** similar to Scrabble
- **Multi-language wordlist support** (German, English, French, Spanish, Italian)
- **Real-time gameplay** via WebSocket connections  
- **Invitation system** for private games
- **Score tracking** with letter and bonus calculations
- **Computer player support** with automatic recreation
- **Intelligent game ending** based on various conditions

## 🏗️ Infrastructure

- **Platform**: Google Cloud Platform
- **Compute**: Cloud Run (serverless containers)  
- **Database**: Cloud SQL PostgreSQL
- **Container Registry**: Google Container Registry
- **Secrets**: Google Secret Manager  
- **Monitoring**: Cloud Logging and Error Reporting

## 🔐 Security Features

- **JWT-based authentication** with refresh tokens
- **Persistent token support** for "remember me" functionality
- **Email verification** with 6-digit codes
- **Admin role management** with fine-grained permissions
- **Contract validation** middleware for API compliance
- **Environment-based configuration** with secure secret management

## 📄 License

MIT