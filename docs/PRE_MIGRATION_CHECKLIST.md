# Pre-Migration Checklist: GCP to Self-Hosted

## 📋 Complete This Checklist Before Migration

This checklist ensures a smooth, secure migration with no data loss or downtime.

---

## ✅ Phase 1: Planning & Preparation

### 1.1 Review Documentation
- [ ] Read `SELF_HOSTED_MIGRATION_PLAN.md` completely
- [ ] Review `QUICK_START_SELF_HOSTED.md`
- [ ] Review `HOSTING_PROVIDER_COMPARISON.md`
- [ ] Understand rollback procedures

### 1.2 Choose Infrastructure
- [ ] Select hosting provider (Recommended: Hetzner CPX31)
- [ ] Choose server location (Recommended: Germany for EU)
- [ ] Verify budget allocation (~$15-20/month)
- [ ] Confirm server specs meet requirements (4 vCPU, 8GB RAM minimum)

### 1.3 Domain & DNS
- [ ] Verify domain ownership and access
- [ ] Access to DNS management (update A records)
- [ ] Consider using Cloudflare for DDoS protection (optional)
- [ ] Plan DNS TTL reduction before migration (set to 300 seconds)
- [ ] Document current DNS records

### 1.4 Backup Strategy
- [ ] Test current GCP backup procedures
- [ ] Identify all data to migrate:
  - [ ] Database (PostgreSQL)
  - [ ] User data
  - [ ] Game data
  - [ ] Wordlist files
  - [ ] Configuration files
- [ ] Plan backup storage (local + cloud)
- [ ] Test backup restoration locally

---

## ✅ Phase 2: Access & Credentials

### 2.1 GCP Access
- [ ] Verify GCP console access
- [ ] Verify `gcloud` CLI installed and authenticated
- [ ] Access to Cloud SQL instance
- [ ] Access to Cloud Run service
- [ ] Export all environment variables from Cloud Run
- [ ] Document all GCP configurations

### 2.2 Server Access Preparation
- [ ] Generate new SSH key pair (if needed)
  ```bash
  ssh-keygen -t ed25519 -C "wordbattle-server"
  ```
- [ ] Save SSH keys securely (password manager)
- [ ] Create server provider account
- [ ] Add payment method to provider
- [ ] Verify identity (Hetzner requires ID verification)

### 2.3 Security Credentials
- [ ] Generate strong passwords for:
  - [ ] Database user password (32+ chars)
  - [ ] Redis password (32+ chars)
  - [ ] Secret key (64+ chars hex)
  - [ ] JWT secret key (64+ chars hex)
- [ ] Store all passwords in secure password manager
- [ ] **Never** commit passwords to git
- [ ] Create backup of all credentials

**Generate passwords:**
```bash
# Database password
openssl rand -base64 32

# Application secrets
openssl rand -hex 32

# Redis password
openssl rand -base64 24
```

---

## ✅ Phase 3: Current State Documentation

### 3.1 Current GCP Configuration
- [ ] Document Cloud Run settings:
  - [ ] CPU allocation
  - [ ] Memory allocation
  - [ ] Concurrency settings
  - [ ] Timeout settings
  - [ ] Environment variables
- [ ] Document Cloud SQL settings:
  - [ ] Instance tier
  - [ ] Database version
  - [ ] Connection settings
  - [ ] Backup schedule
- [ ] Export current `.env` or configuration
- [ ] Take screenshots of GCP console settings

### 3.2 Application State
- [ ] Current number of users: _____________
- [ ] Current number of active games: _____________
- [ ] Current number of total games: _____________
- [ ] Average daily requests: _____________
- [ ] Peak concurrent users: _____________
- [ ] Database size: _____________
- [ ] Average response time: _____________

### 3.3 Performance Baseline
- [ ] Run performance tests on current GCP setup
- [ ] Document current response times
- [ ] Document current error rates
- [ ] Document WebSocket performance
- [ ] Save results for comparison after migration

```bash
# Example performance test
ab -n 1000 -c 10 https://your-current-backend.run.app/health
```

---

## ✅ Phase 4: Test Environment

### 4.1 Local Testing
- [ ] Clone latest code from repository
- [ ] Test Docker build locally
- [ ] Verify all environment variables
- [ ] Test database migrations
- [ ] Test application startup
- [ ] Run unit tests
- [ ] Run integration tests

```bash
cd wordbattle-backend
docker build -t wordbattle-backend:test -f Dockerfile.cloudrun .
docker run -p 8000:8000 wordbattle-backend:test
curl http://localhost:8000/health
```

### 4.2 Staging Environment (Optional but Recommended)
- [ ] Set up smaller/cheaper VPS for staging
- [ ] Deploy application to staging
- [ ] Test complete migration process
- [ ] Verify SSL certificates
- [ ] Test all API endpoints
- [ ] Test WebSocket connections
- [ ] Load test staging environment
- [ ] Document any issues found

---

## ✅ Phase 5: Data Export from GCP

### 5.1 Database Export
- [ ] Test database export process
  ```bash
  gcloud sql export sql INSTANCE_NAME \
    gs://BUCKET_NAME/test-export.sql \
    --project=PROJECT_ID \
    --database=wordbattle
  ```
- [ ] Verify export file integrity
- [ ] Test import to local PostgreSQL
- [ ] Calculate export time (for scheduling)
- [ ] Plan export during low-traffic period

### 5.2 File Assets
- [ ] List all required data files:
  - [ ] `en_words.txt`
  - [ ] `de_words.txt`
  - [ ] `fr_words.txt`
  - [ ] `sp_words.txt`
- [ ] Copy to local machine
- [ ] Verify file integrity (checksums)

### 5.3 Configuration Export
- [ ] Export all environment variables
- [ ] Export secret manager secrets
- [ ] Document API keys and tokens
- [ ] Export SSL certificates (if custom)

---

## ✅ Phase 6: New Server Preparation

### 6.1 Server Provisioning
- [ ] Create server account
- [ ] Provision server (Ubuntu 22.04 LTS)
- [ ] Note server IP address: _____________
- [ ] Configure firewall on provider level (if available)
- [ ] Set up monitoring alerts (if available)

### 6.2 Initial Server Access
- [ ] SSH into server successfully
- [ ] Change root password (if applicable)
- [ ] Update system packages
  ```bash
  apt update && apt upgrade -y
  ```
- [ ] Set timezone correctly
  ```bash
  timedatectl set-timezone Europe/Berlin
  ```
- [ ] Set hostname
  ```bash
  hostnamectl set-hostname wordbattle-prod
  ```

### 6.3 DNS Preparation
- [ ] Reduce DNS TTL to 300 seconds (24h before migration)
- [ ] Prepare DNS A record update
- [ ] Note current DNS settings:
  - Current A record: _____________
  - New A record: _____________
- [ ] Test DNS propagation tools ready

---

## ✅ Phase 7: Communication Plan

### 7.1 User Communication
- [ ] Draft maintenance announcement
- [ ] Plan announcement timing (48h before)
- [ ] Prepare status page (if applicable)
- [ ] Draft "migration complete" announcement
- [ ] Prepare rollback communication

### 7.2 Team Communication
- [ ] Notify team of migration schedule
- [ ] Assign roles and responsibilities
- [ ] Schedule migration time:
  - Date: _____________
  - Start time: _____________
  - Expected duration: _____________
- [ ] Set up communication channel (Slack, Discord, etc.)
- [ ] Prepare escalation contacts

---

## ✅ Phase 8: Monitoring & Alerting

### 8.1 Monitoring Setup
- [ ] Choose monitoring solution:
  - [ ] Basic: health check scripts
  - [ ] Advanced: Prometheus + Grafana
  - [ ] External: UptimeRobot, Pingdom
- [ ] Configure email alerts
- [ ] Set up log aggregation
- [ ] Configure disk space alerts
- [ ] Configure memory usage alerts
- [ ] Configure SSL expiry alerts

### 8.2 Alert Configuration
- [ ] Email for alerts configured: _____________
- [ ] Test email delivery
- [ ] Set up SMS alerts (optional)
- [ ] Configure alert thresholds:
  - [ ] Response time > 1s
  - [ ] Error rate > 1%
  - [ ] Disk usage > 85%
  - [ ] Memory usage > 90%

---

## ✅ Phase 9: Rollback Plan

### 9.1 Rollback Preparation
- [ ] Document rollback procedure
- [ ] Keep GCP resources running during migration
- [ ] Test DNS switch back to GCP
- [ ] Prepare rollback announcement
- [ ] Define rollback triggers:
  - [ ] Error rate > 5%
  - [ ] Response time > 2s for 5 minutes
  - [ ] Database connectivity issues
  - [ ] SSL certificate problems

### 9.2 Rollback Testing
- [ ] Verify GCP backend still works
- [ ] Test DNS switch back to GCP (in staging)
- [ ] Document rollback time (should be < 5 minutes)
- [ ] Assign rollback decision maker: _____________

---

## ✅ Phase 10: Migration Day Preparation

### 10.1 Final Checks (Day Before)
- [ ] All scripts tested and ready
- [ ] All passwords generated and stored
- [ ] Team briefed and available
- [ ] Backup of current production taken
- [ ] Maintenance window announced
- [ ] All documentation reviewed
- [ ] Sleep well! 😴

### 10.2 Migration Day (Morning)
- [ ] Fresh full backup of GCP
- [ ] Verify team availability
- [ ] Test new server accessibility
- [ ] Verify monitoring is working
- [ ] All terminals/tools ready
- [ ] Coffee/tea ready ☕

### 10.3 During Migration
- [ ] Follow checklist step-by-step
- [ ] Don't skip verification steps
- [ ] Document any deviations
- [ ] Take notes of issues
- [ ] Monitor metrics continuously

---

## ✅ Phase 11: Post-Migration

### 11.1 Immediate Validation (First Hour)
- [ ] Health endpoint responding
- [ ] Database queries working
- [ ] WebSocket connections stable
- [ ] User login working
- [ ] Game creation working
- [ ] Game moves working
- [ ] No error spikes in logs
- [ ] Response times acceptable
- [ ] SSL certificate valid

### 11.2 Extended Monitoring (First 24h)
- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Check backup scripts
- [ ] Verify log rotation
- [ ] Check disk space usage
- [ ] Monitor memory usage
- [ ] Verify automated updates
- [ ] Test all endpoints

### 11.3 First Week
- [ ] Daily health checks
- [ ] Review logs daily
- [ ] Monitor user feedback
- [ ] Verify backups working
- [ ] Check SSL auto-renewal
- [ ] Performance comparison to GCP
- [ ] Cost validation

### 11.4 After Stable Week
- [ ] Terminate GCP resources
- [ ] Cancel GCP subscriptions
- [ ] Update all documentation
- [ ] Celebrate success! 🎉
- [ ] Document lessons learned

---

## 📊 Migration Readiness Score

Count your checkmarks:

- **0-30 checks:** ❌ Not ready - more preparation needed
- **31-60 checks:** ⚠️ Getting there - review critical items
- **61-80 checks:** ✅ Good - ready for staging test
- **81-95 checks:** ✅✅ Excellent - ready for production migration
- **96-100 checks:** 🏆 Perfect - you're a pro!

**Your score:** _____ / 100

---

## 🚨 Critical "No-Go" Items

If ANY of these are not checked, **DO NOT PROCEED** with migration:

- [ ] ❗ Full backup of production database tested and verified
- [ ] ❗ Rollback plan documented and tested
- [ ] ❗ Team available during migration window
- [ ] ❗ DNS access verified
- [ ] ❗ New server accessible via SSH
- [ ] ❗ All passwords securely stored
- [ ] ❗ Monitoring and alerts configured
- [ ] ❗ Users notified of maintenance window

---

## 📝 Notes & Custom Items

Add your own checklist items specific to your setup:

- [ ] _______________________________________
- [ ] _______________________________________
- [ ] _______________________________________
- [ ] _______________________________________
- [ ] _______________________________________

---

## 🎯 Ready to Migrate?

Once this checklist is complete, proceed to:
1. `QUICK_START_SELF_HOSTED.md` - For fast migration
2. `SELF_HOSTED_MIGRATION_PLAN.md` - For detailed step-by-step guide

**Estimated Migration Time:**
- Preparation: 4-8 hours
- Server setup: 2-3 hours
- Data migration: 1-2 hours
- Testing & validation: 2-3 hours
- **Total: 1-2 days of active work**

---

**Good luck with your migration! 🚀**

