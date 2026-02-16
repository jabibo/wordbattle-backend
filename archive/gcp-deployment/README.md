# GCP Deployment Documentation (Archived)

**Date Archived**: 2026-02-15  
**Reason**: Project migrated to self-hosted infrastructure

## Contents

This directory contains the original Google Cloud Platform deployment documentation and scripts. These files are kept for historical reference but are no longer used in production.

### Archived Files

- `DEPLOYMENT.md` - GCP deployment guide
- `DEPLOYMENT_CONFIGURATION.md` - Multi-platform configuration
- `MIGRATION_GCP_TO_SELF_HOSTED.md` - Migration documentation
- `Dockerfile.cloudrun` - Cloud Run Dockerfile
- `deploy-unified.sh` - GCP deployment script
- `deployment/` - Detailed GCP deployment guides
- `deploy.*.env` - GCP environment configurations

## Current Production Setup

The WordBattle backend is now hosted on:
- **Platform**: Self-hosted (wordbattle2.de)
- **Infrastructure**: Docker Compose
- **Database**: PostgreSQL (containerized)
- **Cache**: Redis (containerized)
- **Reverse Proxy**: Nginx

## Current Deployment

See the main documentation for self-hosted deployment:
- [docs/SELF_HOSTED_DEPLOYMENT.md](../../docs/SELF_HOSTED_DEPLOYMENT.md)
- Deployment script: `deploy-self-hosted.sh` (backend root)

## Why Archived?

The project was originally deployed on Google Cloud Platform but was migrated to self-hosted infrastructure for:
- Cost optimization
- Greater control over infrastructure
- Simplified deployment process
- No vendor lock-in

These files are preserved for reference in case anyone wants to deploy to GCP in the future.
