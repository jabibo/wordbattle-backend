# Self-Hosted Deployment Guide (wordbattle2.de)

This guide explains how to deploy the WordBattle backend to your self-hosted server at `wordbattle2.de`.

## 📋 Overview

Your production environment runs on a self-hosted server with:
- **Server**: wordbattle2.de
- **Docker containers**: wordbattle-backend, wordbattle-db, wordbattle-redis, wordbattle-nginx
- **Deployment method**: Git-based automated deployment
- **Zero-downtime**: Rolling updates with health checks

## 🚀 Quick Deploy

The fastest way to deploy is using the automated script:

```bash
# From your local machine, in the wordbattle-backend directory
./deploy-self-hosted.sh

# Or deploy a specific branch
./deploy-self-hosted.sh feature/new-feature
```

## 📖 Deployment Process

The deployment script automatically:

1. ✅ **SSH Connection**: Verifies connectivity to the server
2. ✅ **Git Setup**: Initializes or updates git repository on server
3. ✅ **Pull Latest Code**: Fetches and checks out the target branch
4. ✅ **Build Docker Image**: Builds new image with git commit tag
5. ✅ **Backup**: Tags current image as backup
6. ✅ **Container Swap**: Stops old container, starts new one
7. ✅ **Health Check**: Verifies the deployment is working

## 🛠️ Prerequisites

Before deploying, ensure you have:

- **SSH Access**: Ability to SSH to `wordbattle2.de` as root
- **Git Repository**: Your code pushed to the git remote
- **Local Setup**: Deploy script in your local repository

### SSH Access Setup

Test your SSH connection:
```bash
ssh root@wordbattle2.de
```

If you need to set up SSH keys:
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy your public key to the server
ssh-copy-id root@wordbattle2.de
```

## 📂 Server Directory Structure

```
/home/wordbattle/wordbattle/
├── app/                          # Application code
├── data/                         # Wordlist files and data
├── nginx/                        # Nginx configuration
├── ssl/                          # SSL certificates
├── logs/                         # Application logs
├── backups/                      # Database backups
├── scripts/                      # Utility scripts
├── .env                          # Environment variables
├── docker-compose.production.yml # Docker Compose configuration
├── Dockerfile                    # Docker image definition
└── .git/                         # Git repository (created by deployment)
```

## 🔧 Manual Deployment (Advanced)

If you need to deploy manually without the script:

### Step 1: SSH to Server

```bash
ssh root@wordbattle2.de
cd /home/wordbattle/wordbattle
```

### Step 2: Update Code

```bash
# Initialize git if needed
git init
git remote add origin https://github.com/your-username/wordbattle-backend.git

# Pull latest changes
git fetch origin
git checkout main
git pull origin main
```

### Step 3: Build Docker Image

```bash
# Build new image
docker build -t wordbattle-backend:latest .

# Tag with timestamp for tracking
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker tag wordbattle-backend:latest wordbattle-backend:${TIMESTAMP}
```

### Step 4: Update Container

```bash
# Stop old container
docker-compose -f docker-compose.production.yml stop wordbattle-backend
docker-compose -f docker-compose.production.yml rm -f wordbattle-backend

# Start new container
docker-compose -f docker-compose.production.yml up -d wordbattle-backend

# Check status
docker ps | grep wordbattle-backend
```

### Step 5: Verify

```bash
# Check health endpoint
curl https://wordbattle2.de/health

# View logs
docker logs -f wordbattle-backend
```

## 🔍 Monitoring & Troubleshooting

### View Logs

```bash
# Real-time logs
ssh root@wordbattle2.de "docker logs -f wordbattle-backend"

# Last 100 lines
ssh root@wordbattle2.de "docker logs --tail 100 wordbattle-backend"

# Search for errors
ssh root@wordbattle2.de "docker logs wordbattle-backend 2>&1 | grep ERROR"
```

### Check Container Status

```bash
ssh root@wordbattle2.de "docker ps"
```

### Check Health Endpoint

```bash
curl -s https://wordbattle2.de/health | jq
```

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs for errors
ssh root@wordbattle2.de "docker logs wordbattle-backend"

# Check if port is already in use
ssh root@wordbattle2.de "netstat -tulpn | grep 8000"

# Verify Docker Compose file
ssh root@wordbattle2.de "cat /home/wordbattle/wordbattle/docker-compose.production.yml"
```

#### 2. Database Connection Issues

```bash
# Check if database container is running
ssh root@wordbattle2.de "docker ps | grep wordbattle-db"

# Check database connectivity from backend
ssh root@wordbattle2.de "docker exec wordbattle-backend nc -zv wordbattle-db 5432"

# View database logs
ssh root@wordbattle2.de "docker logs wordbattle-db"
```

#### 3. Image Build Failures

```bash
# Check disk space
ssh root@wordbattle2.de "df -h"

# Clean up old images
ssh root@wordbattle2.de "docker image prune -a -f"

# Check Dockerfile syntax
cat Dockerfile
```

#### 4. Git Issues

```bash
# Reset git state
ssh root@wordbattle2.de "cd /home/wordbattle/wordbattle && git reset --hard origin/main"

# Re-clone if needed
ssh root@wordbattle2.de "cd /home/wordbattle && rm -rf wordbattle.old && mv wordbattle wordbattle.old && git clone YOUR_REPO_URL wordbattle"
```

## 🔄 Rollback

If a deployment fails, you can rollback to a previous version:

### Using Backup Image

```bash
ssh root@wordbattle2.de bash << 'EOF'
cd /home/wordbattle/wordbattle

# List available backup images
docker images | grep wordbattle-backend | grep backup

# Stop current container
docker-compose -f docker-compose.production.yml stop wordbattle-backend
docker-compose -f docker-compose.production.yml rm -f wordbattle-backend

# Tag the backup as latest
BACKUP_TAG="backup-20250206_100000"  # Use the tag from list above
docker tag wordbattle-backend:${BACKUP_TAG} wordbattle-backend:latest

# Start container with backup image
docker-compose -f docker-compose.production.yml up -d wordbattle-backend
EOF
```

### Using Git

```bash
ssh root@wordbattle2.de bash << 'EOF'
cd /home/wordbattle/wordbattle

# View commit history
git log --oneline -10

# Reset to previous commit
git reset --hard HEAD~1  # Or specific commit hash

# Rebuild and restart
docker build -t wordbattle-backend:latest .
docker-compose -f docker-compose.production.yml up -d --force-recreate wordbattle-backend
EOF
```

## 🔐 Security Best Practices

1. **Environment Variables**: Keep sensitive data in `.env` file (not in git)
2. **SSH Keys**: Use SSH keys instead of passwords
3. **Firewall**: Ensure only necessary ports are open (80, 443, 22)
4. **Updates**: Regularly update Docker and system packages
5. **Backups**: Automated database backups to `/home/wordbattle/backups/`

## 📊 Deployment History

The deployment script tracks deployments through:
- **Git commits**: Each deployment corresponds to a git commit
- **Docker image tags**: Images tagged with timestamp and commit hash
- **Backup images**: Previous images retained as `backup-TIMESTAMP`

View deployment history:

```bash
# Git history
ssh root@wordbattle2.de "cd /home/wordbattle/wordbattle && git log --oneline -20"

# Docker images
ssh root@wordbattle2.de "docker images | grep wordbattle-backend"
```

## 🔄 CI/CD Integration (Future)

Consider setting up automated deployments with:

### GitHub Actions

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to wordbattle2.de
        run: |
          ./deploy-self-hosted.sh main
        env:
          SSH_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
```

### Webhook-based Deployment

Set up a webhook endpoint that triggers deployment on git push:

```bash
# Install webhook on server
ssh root@wordbattle2.de "apt-get install webhook"

# Configure webhook to run deployment script
# (See GitHub webhook documentation)
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review server logs: `docker logs wordbattle-backend`
3. Check container status: `docker ps`
4. Verify environment configuration: `.env` file
5. Test health endpoint: `curl https://wordbattle2.de/health`

## 🎯 Deployment Checklist

Before deploying to production:

- [ ] Code is committed and pushed to git
- [ ] Tests pass locally
- [ ] Database migrations are ready (if any)
- [ ] Environment variables are configured
- [ ] Backup of current deployment exists
- [ ] Users notified of any expected downtime
- [ ] Monitoring/alerts are active

After deploying:

- [ ] Health endpoint returns healthy status
- [ ] API documentation is accessible
- [ ] WebSocket connections work
- [ ] Database queries are successful
- [ ] No errors in container logs
- [ ] Frontend can connect to backend

---

## 🎉 Quick Reference

```bash
# Deploy to production
./deploy-self-hosted.sh

# Deploy specific branch
./deploy-self-hosted.sh feature/xyz

# View logs
ssh root@wordbattle2.de "docker logs -f wordbattle-backend"

# Check status
ssh root@wordbattle2.de "docker ps"

# Test health
curl https://wordbattle2.de/health

# Rollback (emergency)
ssh root@wordbattle2.de "cd /home/wordbattle/wordbattle && git reset --hard HEAD~1 && docker build -t wordbattle-backend:latest . && docker-compose -f docker-compose.production.yml up -d --force-recreate wordbattle-backend"
```

---

**Happy Deploying! 🚀**
