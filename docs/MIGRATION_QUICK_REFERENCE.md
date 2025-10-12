# Migration Quick Reference Card

## 📋 One-Page Summary

### 💰 Cost Savings
**GCP:** $90-150/month → **Self-Hosted:** $15-25/month  
**Savings:** 75-85% (~$1,200/year)

---

## 🏢 Recommended Provider
**Hetzner CPX31** (Germany)
- 4 vCPU, 8GB RAM, 160GB NVMe
- €12.50/month (~$14)
- Excellent performance and privacy

---

## ⏱️ Time Required
- **Prep:** 4-8 hours
- **Migration:** 5-9 hours  
- **Total Active Work:** 1-2 days
- **With gradual rollout:** 2-3 weeks

---

## 📚 Documentation Guide

| Document | Use Case | Time to Read |
|----------|----------|--------------|
| **MIGRATION_TO_SELF_HOSTED.md** | Start here - Overview | 10 min |
| **PRE_MIGRATION_CHECKLIST.md** | Before you start | 30 min |
| **HOSTING_PROVIDER_COMPARISON.md** | Choose provider | 15 min |
| **QUICK_START_SELF_HOSTED.md** | Experienced admins | 2-3 hours |
| **SELF_HOSTED_MIGRATION_PLAN.md** | Complete guide | 2-3 days |

---

## 🚀 Quick Start Steps

### 1. Preparation (1 day)
```bash
# Choose provider: Hetzner CPX31
# Provision Ubuntu 22.04 server
# Complete pre-migration checklist
# Generate credentials
```

### 2. Server Setup (2-3 hours)
```bash
# Install essentials
apt update && apt upgrade -y
apt install -y docker.io docker-compose ufw fail2ban

# Create user
adduser wordbattle
usermod -aG sudo,docker wordbattle

# Configure firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 3. Application Deployment (1-2 hours)
```bash
# Setup directories
mkdir -p ~/wordbattle/{app,data,backups,logs,nginx}

# Create docker-compose.production.yml
# Deploy application
docker-compose up -d
```

### 4. SSL Setup (15 minutes)
```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Configure auto-renewal
```

### 5. Data Migration (1 hour)
```bash
# Export from GCP
gcloud sql export sql INSTANCE gs://bucket/export.sql

# Import to new server
cat export.sql | docker exec -i wordbattle-db psql -U user -d db
```

---

## 🔐 Essential Security Checklist

- [ ] SSH key-only authentication
- [ ] UFW firewall configured
- [ ] Fail2ban enabled
- [ ] Automated security updates
- [ ] SSL certificates active
- [ ] Strong passwords for all services
- [ ] Database localhost-only
- [ ] Automated backups working

---

## 🛠️ Management Commands

```bash
# After setup, use these simple commands:
wb start          # Start all services
wb stop           # Stop all services
wb restart        # Restart
wb logs [service] # View logs
wb status         # Check status
wb backup         # Manual backup
wb health         # Health check
wb update         # Update app
```

---

## 📊 What Gets Installed

```
Ubuntu 22.04 LTS
├── Nginx (Reverse Proxy + SSL)
├── Docker Compose
│   ├── FastAPI Backend
│   ├── PostgreSQL 15
│   └── Redis
├── UFW (Firewall)
├── Fail2ban (Intrusion Prevention)
├── Certbot (SSL Auto-renewal)
└── Automated Backups
```

---

## ⚡ Key Commands Reference

### Server Management
```bash
# System status
htop                    # Resources
df -h                   # Disk space
docker stats            # Container resources
systemctl status docker # Docker status
```

### Application Management
```bash
# Logs
docker-compose logs -f backend
docker-compose logs -f postgres

# Shell access
docker exec -it wordbattle-backend sh
docker exec -it wordbattle-db psql -U user -d db

# Restart single service
docker-compose restart backend
```

### Maintenance
```bash
# Backup
./scripts/backup.sh

# Update application
cd app && git pull
docker-compose build backend
docker-compose up -d --no-deps backend

# Clean up
docker system prune -f
```

### Security
```bash
# Firewall status
sudo ufw status verbose

# Fail2ban status
sudo fail2ban-client status

# Check SSL
sudo certbot certificates

# Security logs
sudo tail -f /var/log/auth.log
```

---

## 🚨 Emergency Procedures

### Backend Down
```bash
wb restart backend
wb logs backend
# Check .env configuration
# Verify database connectivity
```

### Database Issues
```bash
docker exec -it wordbattle-db psql -U user -d db
# Check connections
# Verify disk space
```

### High Load
```bash
docker stats              # Check resources
htop                      # System resources
wb logs backend           # Check for errors
```

### Rollback to GCP
```bash
# Update DNS back to GCP
# Switch takes 5 minutes with low TTL
# GCP backend still running as backup
```

---

## 💾 Backup Strategy

### Automated Daily Backup
```bash
# Configured in /etc/cron.d/wordbattle-backup
# Runs at 2 AM daily
# Keeps last 30 days
# Location: ~/wordbattle/backups/
```

### Manual Backup
```bash
wb backup
# Creates: backup_YYYYMMDD_HHMMSS.sql.gz
```

### Restore from Backup
```bash
wb restore backup_YYYYMMDD_HHMMSS.sql.gz
# Prompts for confirmation
```

---

## 📈 Monitoring Checklist

### Daily (Automated)
- [x] Health checks
- [x] Backup creation
- [x] Security updates
- [x] Log rotation

### Weekly (Manual)
- [ ] Review logs: `wb logs`
- [ ] Check disk space: `df -h`
- [ ] Verify backups exist
- [ ] Review fail2ban: `sudo fail2ban-client status`

### Monthly (Manual)
- [ ] Test backup restore
- [ ] Update Docker images
- [ ] Review security logs
- [ ] Check SSL expiry

---

## 🎯 Success Metrics

After migration, verify:
- [ ] Health endpoint returns 200 OK
- [ ] Response time < 200ms
- [ ] Error rate < 1%
- [ ] Uptime > 99.9%
- [ ] Backups running daily
- [ ] SSL auto-renewing
- [ ] Cost reduced by 75%+
- [ ] Users experiencing no issues

---

## 🔗 Critical File Locations

```
~/wordbattle/
├── .env                          # Environment variables
├── docker-compose.production.yml # Main config
├── nginx/conf.d/                 # Nginx config
├── data/postgres/                # Database data
├── backups/                      # Database backups
├── logs/                         # Application logs
├── scripts/manage.sh             # Management script
└── app/                          # Application code
```

---

## 📞 Quick Links

- **Full Guide:** [SELF_HOSTED_MIGRATION_PLAN.md](SELF_HOSTED_MIGRATION_PLAN.md)
- **Quick Start:** [QUICK_START_SELF_HOSTED.md](QUICK_START_SELF_HOSTED.md)
- **Providers:** [HOSTING_PROVIDER_COMPARISON.md](HOSTING_PROVIDER_COMPARISON.md)
- **Checklist:** [PRE_MIGRATION_CHECKLIST.md](PRE_MIGRATION_CHECKLIST.md)
- **Overview:** [MIGRATION_TO_SELF_HOSTED.md](MIGRATION_TO_SELF_HOSTED.md)

---

## 🎓 Learning Resources

### Docker
- Official Docs: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/

### Nginx
- Official Docs: https://nginx.org/en/docs/
- Security Guide: https://www.nginx.com/blog/nginx-se-linux-changes-upgrading-rhel-6-rhel-7/

### PostgreSQL
- Official Docs: https://www.postgresql.org/docs/
- Backup Guide: https://www.postgresql.org/docs/current/backup.html

### Ubuntu Server
- Ubuntu Server Guide: https://ubuntu.com/server/docs
- Security: https://ubuntu.com/security

---

## ⚠️ Critical Reminders

1. **NEVER skip backups** - Always backup before changes
2. **Test in staging first** - Don't test in production
3. **Keep GCP running** - Until new server is proven stable
4. **Monitor closely** - Especially first 48 hours
5. **Have rollback ready** - Be able to switch back quickly
6. **Document everything** - Your future self will thank you
7. **Strong passwords** - Use password manager
8. **Regular updates** - Keep system and apps updated

---

## 🎉 Post-Migration Celebration Checklist

- [ ] All services running smoothly
- [ ] Users happy (no complaints)
- [ ] Backups working automatically
- [ ] Monitoring configured
- [ ] Costs reduced by 75%+
- [ ] Team trained on new system
- [ ] Documentation updated
- [ ] GCP resources terminated
- [ ] Money saved celebrated! 🍾

---

**Print this page and keep it handy during migration!**

---

*Quick Reference v1.0 - For WordBattle Self-Hosted Migration*

