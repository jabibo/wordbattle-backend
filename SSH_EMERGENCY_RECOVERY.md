# SSH Issue - Emergency Recovery

**Status**: SSH service may have crashed after configuration changes  
**Time**: 2026-02-15 18:23  

## What Happened

We made changes to SSH configuration and restarted the service. The service appears to have issues starting properly.

## Recovery Steps (When You Have Console Access)

If you have access to the server console (DigitalOcean/Hetzner console, physical access, etc.):

### Option 1: Revert SSH Config

```bash
# Login via console
sudo -i

# Restore backup
cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config

# Restart SSH
systemctl restart sshd

# Check status
systemctl status sshd
```

### Option 2: Check What Went Wrong

```bash
# Check SSH status
systemctl status sshd

# Check SSH logs
journalctl -u sshd -n 50

# Test SSH config
sshd -t

# If config has errors, fix them or restore backup
```

### Option 3: Start SSH Manually

```bash
# If SSH won't start
systemctl stop sshd
/usr/sbin/sshd -D -d

# This will show what's wrong
```

## What We Changed

The changes that may have caused the issue:

```
MaxStartups 20:30:100
MaxSessions 20
ClientAliveInterval 60
ClientAliveCountMax 10
```

## Likely Issue

SSH might not have restarted properly, or there's a syntax issue in the config. The backup is at:
```
/etc/ssh/sshd_config.backup.YYYYMMDD_HHMMSS
```

## Once SSH is Working Again

1. **Test the connection works**:
   ```bash
   ssh root@wordbattle2.de
   ```

2. **The changes we made were**:
   - Your IP whitelisted in fail2ban ✅ (This is good and safe)
   - SSH limits increased (This may need adjustment)

3. **If SSH keeps having issues**, we can use a more conservative approach:
   - Keep your IP whitelisted in fail2ban (most important)
   - Use default SSH settings
   - Accept occasional connection issues during deployment

## Alternative: Don't Change SSH Settings

The safest approach is:
1. **Keep only the fail2ban whitelist** (prevents bans)
2. **Use default SSH settings** (stable and tested)
3. **Add small delays in deployment script** (avoid rapid connections)

We can modify the deployment script to add 2-3 second delays between SSH calls, which would work with default settings.

## Contact Your Hosting Provider

If you can't access the console:
- DigitalOcean: Use the "Recovery Console" or "Droplet Console"  
- Hetzner: Use the "Web Console" in Robot/Cloud Console
- AWS: Use EC2 Instance Connect or Systems Manager Session Manager
- Other providers: Check for web-based console access

##Emergency Contacts

This is not a critical outage:
- Production is still running ✅
- All services are healthy ✅
- Only SSH access is affected
- Your application is still serving users

## Summary

**Good News**:
- Production application is RUNNING and HEALTHY
- Database is working
- Nginx is serving requests
- Only SSH access is temporarily unavailable

**To Fix**:
- Need console access to restart SSH service
- Or wait for automatic recovery (SSH might restart on server reboot)

**Prevention**:
- Test SSH config changes on a development server first
- Always keep a backup of working config (we did this ✅)
- Consider using SSH multiplexing for deployment instead of rapid connections

---

**Don't worry** - your production application is fine and serving users. We just need to restore SSH access through the console when convenient.
