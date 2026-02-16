# Documentation Audit - GCP References

**Date**: 2026-02-15  
**Purpose**: Identify GCP references in documentation for self-hosted setup

## Current Production Setup

- **Hosting**: Self-hosted on wordbattle2.de
- **Infrastructure**: Docker Compose
- **Database**: PostgreSQL (local container)
- **Deployment**: `deploy-self-hosted.sh`

## Files with GCP References

### Files That Should Keep GCP References (Historical/Alternative)

These files document GCP as an **alternative** deployment option:

1. ✅ **`docs/DEPLOYMENT.md`** - GCP deployment guide (keep as alternative)
2. ✅ **`docs/deployment/DEPLOYMENT_GUIDE.md`** - Detailed GCP guide (archived alternative)
3. ✅ **`docs/DEPLOYMENT_CONFIGURATION.md`** - Multi-platform config (keep)
4. ✅ **`docs/MIGRATION_GCP_TO_SELF_HOSTED.md`** - Migration history (keep)
5. ✅ **`docs/README_DEPLOYMENTS.md`** - Index showing both options (keep)

### Files That Need Updates

1. ❌ **`README.md`** - Says "deployed on Google Cloud Platform" (NEEDS UPDATE)
   - Line 5: "deployed on Google Cloud Platform"
   - Line 9-13: Says production is on GCP
   - Line 43: References `Dockerfile.cloudrun`
   - Line 52: Lists "Google Cloud SDK" as prerequisite

## Recommendations

### Option 1: Update README to Reflect Current Setup (Recommended)

Update the main README.md to show:
- Production is self-hosted on wordbattle2.de
- GCP docs available as alternative
- Self-hosted deployment is primary method

### Option 2: Keep Both Deployment Methods Documented

Keep README generic and point to:
- Self-hosted deployment (primary/production)
- GCP deployment (alternative/historical)

## Proposed README Changes

### Current (Incorrect)
```markdown
A FastAPI backend... deployed on Google Cloud Platform.

## 🚀 Current Deployment Status
**Production Environment**: Google Cloud Run  
**Deployment**: Unified deployment pipeline via `deploy-unified.sh`
```

### Proposed (Correct)
```markdown
A FastAPI backend for a multiplayer word game similar to Scrabble.

## 🚀 Current Deployment Status
**Production Environment**: Self-hosted (wordbattle2.de)  
**Current Branch**: `main`  
**Deployment**: Automated via `deploy-self-hosted.sh`

Alternative deployments available (see docs/DEPLOYMENT.md for GCP setup).
```

## Summary

- **Self-hosted docs**: ✅ Clean (no GCP references)
- **GCP docs**: ✅ Properly segregated (in docs/deployment/)
- **Main README**: ❌ Needs update to reflect self-hosted production
- **Deployment index**: ✅ Correctly shows both options

## Action Items

1. Update README.md to reflect self-hosted as primary deployment
2. Keep GCP docs as alternative (don't delete)
3. Ensure all new docs reference self-hosted deployment
4. Update quick start commands to use `deploy-self-hosted.sh`
