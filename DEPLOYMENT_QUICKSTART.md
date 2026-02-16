# 🚀 Quick Start: Deploy to wordbattle2.de

## Fix Production Issue NOW

If you're here because of the production "no wordlist de available" error:

```bash
cd wordbattle-backend
./fix-production-now.sh
```

This will deploy the corrected code and fix the issue.

## Normal Deployment

For regular deployments:

```bash
cd wordbattle-backend
./deploy-self-hosted.sh
```

## What This Does

The deployment script:
1. ✅ Connects to wordbattle2.de via SSH
2. ✅ Pulls latest code from git
3. ✅ Builds new Docker image
4. ✅ Backs up current deployment
5. ✅ Deploys new container
6. ✅ Verifies health

## Prerequisites

- SSH access to wordbattle2.de: `ssh root@wordbattle2.de`
- Git repository URL configured in script (line 18)

## Documentation

- **Full Guide**: [docs/SELF_HOSTED_DEPLOYMENT.md](docs/SELF_HOSTED_DEPLOYMENT.md)
- **Setup Summary**: [SELF_HOSTED_DEPLOYMENT_SETUP.md](SELF_HOSTED_DEPLOYMENT_SETUP.md)
- **All Deployments**: [docs/README_DEPLOYMENTS.md](docs/README_DEPLOYMENTS.md)

## Troubleshooting

```bash
# View logs
ssh root@wordbattle2.de "docker logs -f wordbattle-backend"

# Check status
ssh root@wordbattle2.de "docker ps"

# Test health
curl https://wordbattle2.de/health
```

## Rollback

If something goes wrong:

```bash
ssh root@wordbattle2.de bash << 'EOF'
cd /home/wordbattle/wordbattle
docker images | grep wordbattle-backend | grep backup
# Use the backup tag shown above
docker tag wordbattle-backend:backup-TIMESTAMP wordbattle-backend:latest
docker-compose -f docker-compose.production.yml up -d --force-recreate wordbattle-backend
EOF
```

---

For detailed information, see [docs/SELF_HOSTED_DEPLOYMENT.md](docs/SELF_HOSTED_DEPLOYMENT.md)
