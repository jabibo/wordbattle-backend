# WordBattle: Migration to Self-Hosted Server

## 🎯 Overview

Complete guide to migrate WordBattle from Google Cloud Platform (GCP) to a secure, maintainable self-hosted Ubuntu server.

**Current Setup:** GCP Cloud Run + Cloud SQL  
**Target Setup:** Ubuntu 22.04 + Docker Compose  
**Focus:** Security, Easy Maintenance, Cost Savings

---

## 💰 Cost Savings

| Current (GCP) | Self-Hosted | Savings |
|---------------|-------------|---------|
| $90-150/month | $15-25/month | **75-85%** |
| $1,080-1,800/year | $180-300/year | **$900-1,500/year** |

---

## 📚 Documentation Structure

### 🚀 Quick Start
**For experienced system administrators who want to migrate fast.**

👉 **[QUICK_START_SELF_HOSTED.md](QUICK_START_SELF_HOSTED.md)**
- Condensed migration guide
- All commands ready to copy-paste
- 2-3 hours setup time for experienced admins
- Assumes familiarity with Linux, Docker, and servers

**Use this if you:**
- ✅ Have experience with Linux server administration
- ✅ Are comfortable with Docker and command line
- ✅ Want the fastest path to migration
- ✅ Prefer concise instructions

---

### 📖 Complete Guide
**For detailed explanations, best practices, and security focus.**

👉 **[SELF_HOSTED_MIGRATION_PLAN.md](SELF_HOSTED_MIGRATION_PLAN.md)**
- Comprehensive step-by-step guide
- Detailed explanations of each step
- Security best practices
- Monitoring and maintenance automation
- Troubleshooting guidance
- 8 phases covering complete migration

**Use this if you:**
- ✅ Want to understand every step
- ✅ Are new to self-hosting
- ✅ Want maximum security configuration
- ✅ Need detailed troubleshooting help
- ✅ Want maintenance automation setup

**Contents:**
1. Phase 1: Server Setup & Hardening
2. Phase 2: Docker & Application Setup
3. Phase 3: Data Migration
4. Phase 4: Deployment & SSL Setup
5. Phase 5: Monitoring & Automation
6. Phase 6: Easy Maintenance Commands
7. Phase 7: Gradual Migration Strategy
8. Phase 8: Post-Migration Checklist

---

### 🏢 Provider Comparison
**Choose the right hosting provider for your needs.**

👉 **[HOSTING_PROVIDER_COMPARISON.md](HOSTING_PROVIDER_COMPARISON.md)**
- Detailed comparison of hosting providers
- Price/performance analysis
- Location considerations
- Privacy and GDPR compliance
- Our specific recommendations

**Featured Providers:**
1. **Hetzner (Germany)** - Best Overall ⭐⭐⭐⭐⭐
   - €12.50/month, excellent performance
2. **Netcup (Germany)** - Best Value ⭐⭐⭐⭐
   - €10/month, great price
3. **DigitalOcean (Global)** - Easiest ⭐⭐⭐⭐
   - $24-48/month, best documentation
4. **Contabo (Germany)** - Most Resources ⭐⭐⭐
   - €10.99/month, lots of storage

**Our Recommendation:** Hetzner CPX31

---

### ✅ Pre-Migration Checklist
**Ensure you're fully prepared before starting.**

👉 **[PRE_MIGRATION_CHECKLIST.md](PRE_MIGRATION_CHECKLIST.md)**
- 100+ item comprehensive checklist
- Planning and preparation steps
- Security credential generation
- Testing requirements
- Communication plan
- Rollback preparation
- Migration day checklist

**Critical Sections:**
- Planning & Preparation
- Access & Credentials
- Current State Documentation
- Data Export Preparation
- Rollback Plan
- Post-Migration Validation

**Complete this checklist BEFORE starting migration!**

---

## 🎯 Recommended Migration Path

### For Most Users

```
1. Read this overview                           [5 minutes]
   ↓
2. Review HOSTING_PROVIDER_COMPARISON.md        [10 minutes]
   → Choose provider (we recommend Hetzner)
   ↓
3. Complete PRE_MIGRATION_CHECKLIST.md          [2-4 hours]
   → Prepare all credentials and backups
   ↓
4. Follow SELF_HOSTED_MIGRATION_PLAN.md         [2-3 days]
   → Execute complete migration with testing
   ↓
5. Monitor and validate                         [1 week]
   → Ensure stability before shutting down GCP
```

### For Experienced Admins

```
1. Read this overview                           [5 minutes]
   ↓
2. Skim HOSTING_PROVIDER_COMPARISON.md          [5 minutes]
   → Choose provider quickly
   ↓
3. Review critical items in checklist           [30 minutes]
   → Focus on security and backups
   ↓
4. Follow QUICK_START_SELF_HOSTED.md            [2-3 hours]
   → Fast-track migration
   ↓
5. Monitor and validate                         [1 week]
```

---

## 🔑 Key Features of This Migration

### Security First 🔒
- SSH key-only authentication (no passwords)
- UFW firewall with minimal open ports
- Fail2ban intrusion prevention
- Automated security updates
- SSL/TLS with Let's Encrypt
- Nginx rate limiting and security headers
- Docker security best practices
- Database accessible only from localhost

### Easy Maintenance 🛠️
- One-command management script (`wb start`, `wb stop`, etc.)
- Automated daily backups
- Automated SSL renewal
- Log rotation configured
- Health check monitoring
- Docker Compose for easy updates
- Comprehensive troubleshooting guide

### Cost Effective 💰
- 75-85% cost reduction vs GCP
- No vendor lock-in
- Predictable monthly costs
- No egress fees
- No per-request charges

### Performance ⚡
- Dedicated resources (no cold starts)
- NVMe SSD storage
- 20 Gbps network (Hetzner)
- Lower latency for EU users
- No serverless overhead

---

## 📊 What You'll Get

### Infrastructure Components

```
┌────────────────────────────────────────┐
│  Cloudflare (Optional, Free)          │
│  - DDoS Protection                     │
│  - CDN                                 │
└──────────────┬─────────────────────────┘
               │
               ▼
┌────────────────────────────────────────┐
│  Ubuntu 22.04 LTS Server               │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Nginx (Reverse Proxy)           │ │
│  │  - SSL/TLS                       │ │
│  │  - Rate Limiting                 │ │
│  │  - Security Headers              │ │
│  └────────────┬─────────────────────┘ │
│               │                        │
│  ┌────────────▼─────────────────────┐ │
│  │  Docker Compose                  │ │
│  │  ├─ FastAPI Backend              │ │
│  │  ├─ PostgreSQL 15                │ │
│  │  └─ Redis                        │ │
│  └──────────────────────────────────┘ │
│                                        │
│  Security:                             │
│  - UFW Firewall                        │
│  - Fail2ban                            │
│  - Automated Updates                   │
│                                        │
│  Maintenance:                          │
│  - Automated Backups                   │
│  - Health Monitoring                   │
│  - Log Rotation                        │
└────────────────────────────────────────┘
```

### Management Commands

After setup, you'll have these simple commands:

```bash
wb start          # Start all services
wb stop           # Stop all services
wb restart        # Restart all services
wb logs           # View logs
wb status         # Check status
wb backup         # Manual backup
wb update         # Update application
wb health         # Health check
```

---

## ⏱️ Time Estimates

### Preparation Phase
- Reading documentation: **1-2 hours**
- Choosing provider and signing up: **30 minutes**
- Completing pre-migration checklist: **2-4 hours**
- Testing locally: **1-2 hours**
- **Total Prep: 4-8 hours**

### Migration Phase
- Server setup and hardening: **2-3 hours**
- Application deployment: **1-2 hours**
- Data migration: **1-2 hours**
- SSL setup: **30 minutes**
- Testing and validation: **1-2 hours**
- **Total Migration: 5-9 hours**

### Post-Migration
- Gradual traffic shift: **1 week** (with monitoring)
- Stability verification: **1 week**
- GCP shutdown: **After 2 weeks of stable operation**

**Total Active Work Time: 1-2 days**
**Total Calendar Time: 2-3 weeks** (for careful migration)

---

## ✅ Success Criteria

Migration is successful when:

### Technical
- [x] All services running and healthy
- [x] SSL certificates active and auto-renewing
- [x] Database migrated with zero data loss
- [x] All API endpoints responding correctly
- [x] WebSocket connections stable
- [x] Response times ≤ current GCP performance
- [x] No errors in logs

### Operational
- [x] Automated backups working
- [x] Monitoring and alerts configured
- [x] Health checks passing
- [x] One-command management working
- [x] Documentation updated

### Business
- [x] Users experiencing no disruption
- [x] 99.9%+ uptime achieved
- [x] Cost reduced by 75-85%
- [x] Team comfortable with new setup

---

## 🚨 Risk Mitigation

### Before Migration
- ✅ Complete pre-migration checklist
- ✅ Test entire process in staging
- ✅ Full backup of production data
- ✅ Documented rollback procedure
- ✅ Team trained and available

### During Migration
- ✅ Gradual traffic shift (not immediate)
- ✅ Keep GCP running as backup
- ✅ Real-time monitoring
- ✅ Ready to rollback within 5 minutes
- ✅ Clear communication with users

### After Migration
- ✅ Enhanced monitoring for first week
- ✅ Daily health checks
- ✅ GCP resources kept for 1-2 weeks
- ✅ Regular backup verification

---

## 🛟 Support & Troubleshooting

### During Migration
If you encounter issues:
1. **Check logs:** `wb logs backend`
2. **Verify health:** `wb health`
3. **Review documentation:** Detailed troubleshooting in full guide
4. **Rollback if needed:** Follow rollback procedure

### Common Issues & Solutions

**Backend won't start:**
```bash
wb logs backend
# Check environment variables in .env
# Verify database connection
```

**SSL certificate issues:**
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

**Database connection errors:**
```bash
docker exec -it wordbattle-db psql -U wordbattle_user
# Check if database is accessible
```

**High resource usage:**
```bash
docker stats
htop
# Check for memory leaks or excessive load
```

---

## 📞 Additional Resources

### Documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Current GCP deployment (reference)
- [DEPLOYMENT_CONFIGURATION.md](DEPLOYMENT_CONFIGURATION.md) - Config reference
- [ARCHITECTURE.md](ARCHITECTURE.md) - Application architecture
- [DATABASE.md](DATABASE.md) - Database schema and management

### External Resources
- [Docker Documentation](https://docs.docker.com/)
- [Ubuntu Server Guide](https://ubuntu.com/server/docs)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

## 🎉 Benefits After Migration

### For You (Developer/Admin)
- ✅ Full control over infrastructure
- ✅ No vendor lock-in
- ✅ Learn valuable self-hosting skills
- ✅ Ability to customize anything
- ✅ Transparent costs
- ✅ Better understanding of your stack

### For Your Project
- ✅ 75-85% cost reduction
- ✅ Predictable monthly costs
- ✅ Better performance (dedicated resources)
- ✅ No cold starts
- ✅ EU data residency (GDPR)
- ✅ No surprise bills

### For Your Users
- ✅ Same or better performance
- ✅ Lower latency (especially EU)
- ✅ No noticeable change
- ✅ Improved privacy (EU servers)
- ✅ Potentially faster response times

---

## 🚀 Ready to Start?

### Quick Decision Tree

**Are you experienced with Linux servers?**
- **Yes** → Start with [QUICK_START_SELF_HOSTED.md](QUICK_START_SELF_HOSTED.md)
- **No** → Start with [SELF_HOSTED_MIGRATION_PLAN.md](SELF_HOSTED_MIGRATION_PLAN.md)

**Do you know which provider to use?**
- **No** → Read [HOSTING_PROVIDER_COMPARISON.md](HOSTING_PROVIDER_COMPARISON.md)
- **Yes** → Continue to checklist

**Have you done the prep work?**
- **No** → Complete [PRE_MIGRATION_CHECKLIST.md](PRE_MIGRATION_CHECKLIST.md)
- **Yes** → Start migration!

---

## 📝 Migration Phases Overview

### Phase 1: Planning (1 day)
- Review all documentation
- Choose hosting provider
- Complete pre-migration checklist
- Set migration date

### Phase 2: Preparation (1-2 days)
- Provision server
- Generate credentials
- Export GCP data
- Test backup/restore

### Phase 3: Migration (1 day)
- Setup server
- Deploy application
- Migrate data
- Configure SSL
- Test thoroughly

### Phase 4: Traffic Shift (1 week)
- Day 1-2: 10% traffic to new server
- Day 3-4: 50% traffic
- Day 5-7: 100% traffic
- Monitor continuously

### Phase 5: Stabilization (1 week)
- Monitor daily
- Fix any issues
- Optimize performance
- Verify backups

### Phase 6: Cleanup (After 2 weeks)
- Shut down GCP resources
- Cancel subscriptions
- Update documentation
- Celebrate! 🎉

---

## 🏆 Expected Outcomes

### Technical Improvements
- Dedicated resources (no shared compute)
- Faster response times (no cold starts)
- Better WebSocket performance
- Full control over configuration
- Easier debugging and monitoring

### Cost Improvements
- **Monthly:** $90-150 → $15-25 (85% savings)
- **Yearly:** $1,080-1,800 → $180-300
- **5-Year:** $5,400-9,000 → $900-1,500
- **Total 5-Year Savings: $4,500-7,500** 💰

### Operational Improvements
- Simple one-command management
- Automated backups and updates
- No vendor lock-in
- Better understanding of your infrastructure
- Skills that transfer to other projects

---

## ⚠️ Important Notes

1. **Keep GCP running during migration** - Don't shut down until new server is stable
2. **Test everything** - Never skip testing phases
3. **Backup before migration** - Full backup of all data
4. **Gradual traffic shift** - Don't switch 100% immediately
5. **Monitor closely** - Especially first 48 hours
6. **Have rollback ready** - Ability to switch back to GCP in minutes
7. **Don't rush** - Better to take extra time than have downtime

---

## 📅 Recommended Timeline

```
Week -2: Planning & Preparation
  ├─ Review all documentation
  ├─ Choose hosting provider
  ├─ Complete pre-migration checklist
  └─ Announce maintenance window to users

Week -1: Setup & Testing
  ├─ Provision server
  ├─ Complete server setup
  ├─ Deploy to staging
  └─ Test complete migration process

Week 0: Migration Week
  ├─ Monday: Final preparation & backup
  ├─ Tuesday: Execute migration
  ├─ Wednesday: Testing & validation
  ├─ Thursday: Start 10% traffic shift
  ├─ Friday: Increase to 50% traffic
  └─ Weekend: Monitor closely

Week +1: Stabilization
  ├─ Complete traffic shift to 100%
  ├─ Daily monitoring and optimization
  ├─ Verify all automated tasks
  └─ User feedback collection

Week +2: Cleanup
  ├─ Verify stability
  ├─ Shut down GCP resources
  ├─ Update all documentation
  └─ Post-mortem and lessons learned
```

---

## ✉️ Questions?

Before starting:
1. Review all four documents in this guide
2. Complete the pre-migration checklist
3. Test in a staging environment if possible
4. Ensure you have backups
5. Ensure you have a rollback plan

**Remember:** It's better to take extra time preparing than to rush and cause downtime!

---

## 🎯 Next Steps

1. **Choose your path:**
   - Experienced: [QUICK_START_SELF_HOSTED.md](QUICK_START_SELF_HOSTED.md)
   - Detailed: [SELF_HOSTED_MIGRATION_PLAN.md](SELF_HOSTED_MIGRATION_PLAN.md)

2. **Choose your provider:**
   - Review: [HOSTING_PROVIDER_COMPARISON.md](HOSTING_PROVIDER_COMPARISON.md)
   - Recommended: Hetzner CPX31

3. **Prepare for migration:**
   - Complete: [PRE_MIGRATION_CHECKLIST.md](PRE_MIGRATION_CHECKLIST.md)

4. **Execute migration:**
   - Follow chosen guide step-by-step
   - Don't skip verification steps
   - Monitor continuously

5. **Verify success:**
   - All services healthy
   - Users happy
   - Costs reduced
   - Backups working

---

**Good luck with your migration! You've got this! 🚀**

*This migration guide was created with a focus on security, maintainability, and ease of use. Follow the steps carefully and you'll have a professional, cost-effective self-hosted setup.*

