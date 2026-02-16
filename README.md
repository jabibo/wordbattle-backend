# WordBattle Backend

[![Coverage](https://img.shields.io/badge/coverage-83%25-green.svg)](https://github.com/yourusername/wordbattle-backend)

A FastAPI backend for a multiplayer word game similar to Scrabble.

## 🚀 Current Deployment Status

**Production Environment**: Self-hosted (wordbattle2.de)  
**Current Branch**: `main`  
**Deployment**: Automated deployment via `deploy-self-hosted.sh`  

The application is running on a self-hosted Docker infrastructure with PostgreSQL, Redis, and Nginx.

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
├── deploy-self-hosted.sh         # 🚀 Production deployment script
├── Dockerfile                    # Docker configuration
└── requirements.txt              # Python dependencies
```

## 🔧 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git
- SSH access to production server (for deployment)

### Local Development

**Option A: Docker (recommended for push notifications)**

```bash
cd wordbattle-backend

# Optional: Copy .env for overrides
cp .env.dev.example .env

# For push notifications: Place firebase-credentials.json in config/
# See docs/PUSH_NOTIFICATIONS_DEV_SETUP.md

docker compose -f docker-compose.dev.yml up -d --build
# API at http://localhost:8000
```

**Option B: Python venv**

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

### Self-Hosted Production (wordbattle2.de)

Deploy to your self-hosted server:

```bash
./deploy-self-hosted.sh
```

The script automatically handles:
- ✅ Git repository management on server
- ✅ Docker image building with latest code
- ✅ Container deployment with health checks
- ✅ Automatic backups before deployment
- ✅ Zero-downtime rolling updates

**Documentation**: [docs/SELF_HOSTED_DEPLOYMENT.md](docs/SELF_HOSTED_DEPLOYMENT.md)

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

- **Platform**: Self-hosted (wordbattle2.de)
- **Compute**: Docker containers
- **Database**: PostgreSQL (containerized)
- **Cache**: Redis (containerized)
- **Reverse Proxy**: Nginx
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