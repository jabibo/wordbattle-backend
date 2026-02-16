# SSH Security Configuration - Production Server

**Date**: 2026-02-15  
**Server**: wordbattle2.de  
**Status**: Optimized for deployment scripts

## Issue

During deployment, SSH connections were frequently dropping with "Connection refused" errors. This was caused by **fail2ban** security software blocking rapid connection attempts.

## Root Cause

- **fail2ban** was monitoring SSH and temporarily blocking IPs making rapid connections
- Default SSH limits were too conservative for deployment scripts
- Deployment scripts make multiple rapid SSH connections, triggering security measures

## Changes Made

### 1. Whitelisted Your IP in fail2ban

**File**: `/etc/fail2ban/jail.local`

```ini
[DEFAULT]
ignoreip = 127.0.0.1/8 ::1 95.89.119.13
```

Your IP (95.89.119.13) is now permanently whitelisted and will never be blocked by fail2ban.

### 2. Optimized SSH Configuration

**File**: `/etc/ssh/sshd_config`

Added/updated these settings:

```
MaxStartups 20:30:100
MaxSessions 20
ClientAliveInterval 60
ClientAliveCountMax 10
```

**What these do**:
- **MaxStartups**: Allows up to 100 concurrent connection attempts (was default ~10)
- **MaxSessions**: Allows 20 multiplexed sessions per connection (was default 10)
- **ClientAliveInterval**: Sends keepalive every 60 seconds
- **ClientAliveCountMax**: Allows 10 missed keepalives before disconnect (10 minutes total)

### 3. fail2ban Settings

Current configuration:
- **Bantime**: 3600 seconds (1 hour)
- **Findtime**: 600 seconds (10 minutes)
- **Maxretry**: 3 attempts
- **Your IP**: Whitelisted (never banned)

## Benefits

✅ **Deployment scripts now work reliably** - No more connection refused errors  
✅ **Your IP is protected** - Won't be blocked even with many connections  
✅ **Connections stay alive longer** - Better for long-running deployments  
✅ **Security maintained** - Other IPs are still protected by fail2ban

## Current fail2ban Bans

Currently banned IPs (attacking the server):
- 146.190.224.236
- 161.35.149.219
- 92.118.39.76

Your IP (95.89.119.13) is **NOT** on this list and never will be.

## Testing

Test that rapid connections work:

```bash
for i in 1 2 3 4 5; do 
  ssh root@wordbattle2.de "echo 'Test $i'" 
  sleep 1
done
```

Should complete without any "Connection refused" errors.

## Managing fail2ban

### Check Status

```bash
ssh root@wordbattle2.de "fail2ban-client status sshd"
```

### View Banned IPs

```bash
ssh root@wordbattle2.de "fail2ban-client get sshd banned"
```

### Unban an IP (if needed)

```bash
ssh root@wordbattle2.de "fail2ban-client set sshd unbanip <IP_ADDRESS>"
```

### Add More Whitelisted IPs

Edit `/etc/fail2ban/jail.local`:

```bash
ssh root@wordbattle2.de "nano /etc/fail2ban/jail.local"
```

Add IPs to the `ignoreip` line, space-separated:

```ini
ignoreip = 127.0.0.1/8 ::1 95.89.119.13 YOUR_OTHER_IP
```

Then restart fail2ban:

```bash
ssh root@wordbattle2.de "systemctl restart fail2ban"
```

## Backup

SSH config backup created at:
- `/etc/ssh/sshd_config.backup.YYYYMMDD_HHMMSS`

To restore if needed:

```bash
ssh root@wordbattle2.de "cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config && systemctl restart sshd"
```

## Security Notes

- **fail2ban is still active** - Protects against brute force attacks from unknown IPs
- **Only your IP is whitelisted** - Other IPs are still monitored and blocked if suspicious
- **SSH still requires key authentication** - Password authentication remains disabled
- **Firewall (ufw) is still active** - Only necessary ports are open

## Deployment Scripts

All deployment scripts will now work without interruption:

```bash
# These should all work smoothly now:
./deploy-self-hosted.sh main
./deploy-resilient.sh main
./fix-production-now.sh
```

## Monitoring

Check fail2ban logs:

```bash
ssh root@wordbattle2.de "tail -f /var/log/fail2ban.log"
```

Check SSH auth logs:

```bash
ssh root@wordbattle2.de "tail -f /var/log/auth.log | grep sshd"
```

## Summary

✅ **Your IP whitelisted** - Never blocked by fail2ban  
✅ **SSH limits increased** - Handles rapid deployment connections  
✅ **Keepalive configured** - Connections stay alive longer  
✅ **Security maintained** - Unknown IPs still protected  
✅ **Backups created** - Can revert if needed

**The SSH connection issues during deployment should now be completely resolved.**

---

## Quick Reference

```bash
# Check if your IP is whitelisted
ssh root@wordbattle2.de "fail2ban-client get sshd ignoreip"

# Check SSH settings
ssh root@wordbattle2.de "grep -E 'MaxStartups|MaxSessions|ClientAlive' /etc/ssh/sshd_config | grep -v '^#'"

# View fail2ban status
ssh root@wordbattle2.de "fail2ban-client status sshd"

# Test deployment script
cd wordbattle-backend && ./deploy-self-hosted.sh main
```
