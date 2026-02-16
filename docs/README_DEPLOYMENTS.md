# WordBattle Deployment

Complete guide for deploying the WordBattle backend to your self-hosted server.

## 📚 Documentation

- **[SELF_HOSTED_DEPLOYMENT.md](SELF_HOSTED_DEPLOYMENT.md)** - Complete deployment guide
- **Quick deploy**: `./deploy-self-hosted.sh` from the backend root directory

## 🚀 Quick Start

Deploy to production:

```bash
cd wordbattle-backend
./deploy-self-hosted.sh
```

## 📋 Prerequisites

- SSH access to wordbattle2.de
- Git repository URL configured
- Docker and Docker Compose on server

## 🛠️ Available Scripts

| Script | Purpose | Location |
|--------|---------|----------|
| `deploy-self-hosted.sh` | Deploy to wordbattle2.de | Backend root |
| `deploy-resilient.sh` | Deploy with retry logic | Backend root |
| `recovery-script.sh` | Emergency recovery | Backend root |

## 🔍 Deployment Process

The deployment script automatically:
- ✅ Connects to server via SSH
- ✅ Pulls latest code from git
- ✅ Builds new Docker image
- ✅ Creates backup of current deployment
- ✅ Deploys new container
- ✅ Verifies health

## 🆘 Troubleshooting

Common issues and solutions:

1. **SSH Connection Failed**
   - Check SSH keys: `ssh root@wordbattle2.de`
   - Verify firewall rules
   - Check if your IP is whitelisted in fail2ban

2. **Container Won't Start**
   - Check logs: `ssh root@wordbattle2.de "docker logs wordbattle-backend"`
   - Verify environment variables in `.env` file
   - Check database connectivity

3. **Build Failures**
   - Check disk space on server
   - Verify Dockerfile syntax
   - Ensure all dependencies are available

See [SELF_HOSTED_DEPLOYMENT.md](SELF_HOSTED_DEPLOYMENT.md) for detailed troubleshooting.

## 📞 Support

For deployment issues:
1. Check the deployment guide
2. Review container logs
3. Verify environment configuration
4. Test health endpoints

## 🔐 Security

- SSH uses key-based authentication
- fail2ban protects against brute force
- Your IP should be whitelisted (see SSH_SECURITY_CONFIGURATION.md)
- Firewall (ufw) restricts access to necessary ports

---

**Quick Links:**
- [Self-Hosted Deployment Guide](SELF_HOSTED_DEPLOYMENT.md)
- [SSH Security Configuration](../SSH_SECURITY_CONFIGURATION.md)
- [Main README](../../README.md)
