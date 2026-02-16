# Deployment Ready - Awaiting SSH Connection

**Status**: Deployment script is ready but SSH connection to wordbattle2.de is currently unavailable.

## What's Ready

✅ Deployment script created and configured  
✅ Git repository URL set to: `https://github.com/jabibo/wordbattle-backend.git`  
✅ All documentation complete  
✅ SSH connectivity confirmed earlier (but currently down)

## Current Issue

The SSH connection to wordbattle2.de is currently refusing connections:
```
ssh: connect to host wordbattle2.de port 22: Connection refused
```

This is likely due to:
- Temporary network issue
- Server firewall/rate limiting
- SSH service temporarily unavailable

## When SSH is Available Again

### Test Connection First

```bash
ssh root@wordbattle2.de
```

If this works, proceed to deployment.

### Run the Deployment

Simply execute:

```bash
cd /Users/janbinge/git/wordbattle/wordbattle-backend
./deploy-self-hosted.sh main
```

Or use the quick fix script:

```bash
cd /Users/janbinge/git/wordbattle/wordbattle-backend
./fix-production-now.sh
```

## What the Deployment Will Do

1. **Initialize Git Repository** on the server (first time)
   - Backs up current `/home/wordbattle/wordbattle` directory
   - Initializes git repository
   - Adds remote: `https://github.com/jabibo/wordbattle-backend.git`
   - Checks out main branch

2. **Build Docker Image**
   - Pulls latest code from main branch
   - Builds new Docker image with current code (including the wordlist fix)
   - Tags image with timestamp and commit hash

3. **Deploy**
   - Backs up current running image
   - Stops old container
   - Starts new container with updated code
   - Runs health checks

## Expected Output

When the deployment runs successfully, you'll see:

```
==========================================
  WordBattle Self-Hosted Deployment
==========================================

ℹ Target server: wordbattle2.de
ℹ Target branch: main
ℹ Container: wordbattle-backend

ℹ Step 1/7: Checking SSH connectivity...
✅ SSH connection established

ℹ Step 2/7: Setting up git repository on server...
✅ Git repository ready

ℹ Step 3/7: Building new Docker image...
✅ Docker image built

ℹ Step 4/7: Creating backup of current state...
✅ Backup created

ℹ Step 5/7: Stopping old container...
✅ Old container removed

ℹ Step 6/7: Starting new container...
✅ New container started

ℹ Step 7/7: Verifying deployment...
✅ Health check passed

==========================================
  Deployment Summary
==========================================

Git commit: fd54d23 Add production server deployment status analysis
Container status: wordbattle-backend Up X seconds wordbattle-backend:latest

✅ Deployment completed!

ℹ Access your application at: https://wordbattle2.de
ℹ API documentation: https://wordbattle2.de/docs
ℹ Health check: https://wordbattle2.de/health
```

## Troubleshooting SSH Issues

### Check if SSH is Running

```bash
ssh root@wordbattle2.de
```

### If Connection Refused Persists

Try these diagnostics:

1. **Check if server is reachable**:
   ```bash
   ping wordbattle2.de
   ```

2. **Check if SSH port is open**:
   ```bash
   nc -zv wordbattle2.de 22
   ```

3. **Try from different network** (if on VPN, try without or vice versa)

4. **Wait a few minutes** - The server might be temporarily blocking connections due to rate limiting

### Alternative: Manual Deployment

If SSH remains unavailable, you can provide the deployment script to someone with direct server access:

1. Copy `deploy-self-hosted.sh` to the server
2. Run it from the server directly
3. Or follow the manual deployment steps in `docs/SELF_HOSTED_DEPLOYMENT.md`

## Post-Deployment Verification

Once deployment completes, verify:

1. **Health Check**:
   ```bash
   curl https://wordbattle2.de/health
   ```

2. **Check Logs**:
   ```bash
   ssh root@wordbattle2.de "docker logs --tail 50 wordbattle-backend"
   ```

3. **Test Wordlist** (the original issue):
   - Try creating a new game with German language
   - Should no longer see "no wordlist de available" error

## The Fix

The deployment will resolve the production issue because:

✅ **Root Cause**: Production was running code from November 8, 2025 with incorrect import  
❌ **Old Code**: `from app.database import get_db` (wrong)  
✅ **New Code**: `from app.db import get_db` (correct)  

The deployment pulls the latest code which has this fix.

## Files Created

All files are ready in your repository:

- ✅ `deploy-self-hosted.sh` - Main deployment script
- ✅ `fix-production-now.sh` - Quick fix wrapper
- ✅ `docs/SELF_HOSTED_DEPLOYMENT.md` - Full documentation
- ✅ `SELF_HOSTED_DEPLOYMENT_SETUP.md` - Setup summary
- ✅ `DEPLOYMENT_QUICKSTART.md` - Quick reference

## Next Steps

1. **Wait for SSH** - Connection should be restored soon
2. **Test SSH** - Run `ssh root@wordbattle2.de`
3. **Run Deployment** - Execute `./deploy-self-hosted.sh main`
4. **Verify Fix** - Check health endpoint and test game creation

---

**The deployment system is fully ready. Just waiting for SSH connectivity to be restored.**

You can monitor SSH availability with:
```bash
watch -n 5 'ssh -o ConnectTimeout=2 root@wordbattle2.de "echo OK" 2>&1'
```

Or periodically test:
```bash
ssh root@wordbattle2.de
```

Once connected, simply run:
```bash
cd /Users/janbinge/git/wordbattle/wordbattle-backend && ./deploy-self-hosted.sh main
```
