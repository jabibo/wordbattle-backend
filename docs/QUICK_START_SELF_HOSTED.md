# WordBattle Self-Hosted: Quick Start Guide

## 🚀 Fast Track Migration (For Experienced Admins)

This is a condensed version of the full migration plan. For detailed explanations, see `SELF_HOSTED_MIGRATION_PLAN.md`.

---

## Prerequisites

- Ubuntu 22.04 LTS server (4 vCPU, 8GB RAM minimum)
- Root/sudo access
- Domain name pointed to server
- SSH access configured

---

## Step 1: Initial Server Setup (30 minutes)

```bash
# Run as root
apt update && apt upgrade -y

# Install essentials
apt install -y curl wget git vim ufw fail2ban unattended-upgrades docker.io docker-compose

# Create user
adduser --disabled-password wordbattle
usermod -aG sudo,docker wordbattle

# Setup SSH keys (add your public key)
mkdir -p /home/wordbattle/.ssh
nano /home/wordbattle/.ssh/authorized_keys  # Paste your SSH public key
chmod 700 /home/wordbattle/.ssh
chmod 600 /home/wordbattle/.ssh/authorized_keys
chown -R wordbattle:wordbattle /home/wordbattle/.ssh

# Harden SSH
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

---

## Step 2: Application Setup (20 minutes)

```bash
# Switch to wordbattle user
su - wordbattle

# Create directory structure
mkdir -p ~/wordbattle/{app,data,backups,logs,ssl,scripts,nginx/conf.d}
mkdir -p ~/wordbattle/data/{postgres,redis}

cd ~/wordbattle

# Generate secrets
openssl rand -hex 32 > .db_password
openssl rand -hex 32 > .secret_key
openssl rand -hex 32 > .jwt_secret
openssl rand -base64 24 > .redis_password

# Create .env file
cat > .env << EOF
DB_USER=wordbattle_user
DB_PASSWORD=$(cat .db_password)
DB_NAME=wordbattle_prod
SECRET_KEY=$(cat .secret_key)
JWT_SECRET_KEY=$(cat .jwt_secret)
REDIS_PASSWORD=$(cat .redis_password)
ALLOWED_ORIGINS=https://yourdomain.com
EOF

chmod 600 .env
```

---

## Step 3: Download Configuration Files (10 minutes)

Create `docker-compose.production.yml`:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    container_name: wordbattle-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "127.0.0.1:5432:5432"
    networks:
      - wordbattle-net

  backend:
    image: wordbattle-backend:latest
    container_name: wordbattle-backend
    restart: unless-stopped
    build:
      context: ./app
      dockerfile: Dockerfile
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: ${DB_NAME}
      DB_USER: ${DB_USER}
      DB_PASSWORD: ${DB_PASSWORD}
      ENVIRONMENT: production
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS}
    depends_on:
      - postgres
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - ./logs/app:/app/logs
    networks:
      - wordbattle-net

  nginx:
    image: nginx:alpine
    container_name: wordbattle-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
    networks:
      - wordbattle-net

  redis:
    image: redis:7-alpine
    container_name: wordbattle-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - ./data/redis:/data
    ports:
      - "127.0.0.1:6379:6379"
    networks:
      - wordbattle-net

networks:
  wordbattle-net:
    driver: bridge
```

Create `nginx/conf.d/wordbattle.conf`:

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/certbot/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/certbot/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Step 4: Deploy Application (15 minutes)

```bash
cd ~/wordbattle

# Clone your application
git clone https://github.com/yourusername/wordbattle-backend.git app

# Build and start
docker-compose -f docker-compose.production.yml up -d

# Check logs
docker-compose logs -f
```

---

## Step 5: Setup SSL (10 minutes)

```bash
# Install certbot (as root)
sudo apt install -y certbot

# Stop nginx temporarily
docker-compose stop nginx

# Get certificate
sudo certbot certonly --standalone \
  -d yourdomain.com \
  --non-interactive \
  --agree-tos \
  --email your-email@example.com

# Copy certificates
sudo cp -r /etc/letsencrypt ~/wordbattle/ssl/certbot/
sudo chown -R wordbattle:wordbattle ~/wordbattle/ssl

# Setup auto-renewal (as root)
echo "0 3 * * * root certbot renew --quiet --deploy-hook 'docker exec wordbattle-nginx nginx -s reload'" | sudo tee /etc/cron.d/certbot-renew

# Start nginx
docker-compose start nginx

# Test
curl https://yourdomain.com/health
```

---

## Step 6: Data Migration (30 minutes)

```bash
# On GCP (your local machine):
gcloud sql export sql wordbattle-db-prod \
  gs://your-bucket/export.sql \
  --project=wordbattle-1748668162 \
  --database=wordbattle

gsutil cp gs://your-bucket/export.sql ./backup/

# Transfer to new server
scp backup/export.sql wordbattle@your-server-ip:~/wordbattle/backups/

# On new server:
cd ~/wordbattle
cat backups/export.sql | docker exec -i wordbattle-db psql -U $DB_USER -d $DB_NAME

# Verify
docker exec wordbattle-db psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM users;"
```

---

## Step 7: Setup Automated Backups (10 minutes)

```bash
# Create backup script
cat > ~/wordbattle/scripts/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/wordbattle/wordbattle/backups"
docker exec wordbattle-db pg_dump -U $DB_USER $DB_NAME | gzip > ${BACKUP_DIR}/backup_${DATE}.sql.gz
find ${BACKUP_DIR} -name "backup_*.sql.gz" -mtime +30 -delete
EOF

chmod +x ~/wordbattle/scripts/backup.sh

# Add cron job (as root)
echo "0 2 * * * wordbattle /home/wordbattle/wordbattle/scripts/backup.sh" | sudo tee /etc/cron.d/wordbattle-backup
```

---

## Step 8: Create Management Script (5 minutes)

```bash
cat > ~/wordbattle/scripts/manage.sh << 'EOF'
#!/bin/bash
cd /home/wordbattle/wordbattle

case "$1" in
    start)   docker-compose -f docker-compose.production.yml up -d ;;
    stop)    docker-compose -f docker-compose.production.yml stop ;;
    restart) docker-compose -f docker-compose.production.yml restart ;;
    logs)    docker-compose -f docker-compose.production.yml logs -f ${2:-backend} ;;
    status)  docker-compose -f docker-compose.production.yml ps ;;
    backup)  ./scripts/backup.sh ;;
    health)  curl -f http://localhost:8000/health ;;
    *)       echo "Usage: $0 {start|stop|restart|logs|status|backup|health}" ;;
esac
EOF

chmod +x ~/wordbattle/scripts/manage.sh

# Add aliases
echo "alias wb='~/wordbattle/scripts/manage.sh'" >> ~/.bashrc
source ~/.bashrc
```

---

## Common Commands

```bash
# Start/Stop
wb start
wb stop
wb restart

# Monitor
wb logs backend
wb logs postgres
wb status

# Maintenance
wb backup
wb health

# Database access
docker exec -it wordbattle-db psql -U wordbattle_user -d wordbattle_prod

# Update application
cd ~/wordbattle/app && git pull
docker-compose build backend
docker-compose up -d --no-deps backend
```

---

## Quick Health Check

```bash
# Test all components
curl https://yourdomain.com/health     # Should return 200 OK
wb health                               # Should show "OK"
wb status                               # All containers should be "Up"
docker exec wordbattle-db pg_isready   # Should show "accepting connections"
```

---

## Troubleshooting

**Backend won't start:**
```bash
wb logs backend
# Check .env file has correct values
# Verify database is accessible
```

**Database connection error:**
```bash
wb logs postgres
docker exec -it wordbattle-db psql -U wordbattle_user -d wordbattle_prod
```

**SSL certificate issues:**
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

**Nginx errors:**
```bash
wb logs nginx
docker exec wordbattle-nginx nginx -t
```

---

## Security Checklist

- [ ] SSH password authentication disabled
- [ ] Firewall configured (ports 22, 80, 443 only)
- [ ] Fail2ban active
- [ ] Automated security updates enabled
- [ ] SSL certificates installed and auto-renewing
- [ ] Strong passwords generated for all services
- [ ] Database only accessible from localhost
- [ ] Automated backups configured
- [ ] .env file has restricted permissions (600)

---

## Cost Estimate

**Recommended Providers:**
- Hetzner CPX31: €12.50/month (~$14)
- Netcup VPS 2000: €10/month (~$11)
- DigitalOcean: $24/month

**Total:** ~$11-24/month (vs $90-150 on GCP)
**Savings:** 75-85%

---

## Next Steps After Migration

1. Update frontend to point to new backend URL
2. Test all functionality thoroughly
3. Monitor logs for first 24 hours
4. Set up additional monitoring (optional)
5. Update documentation with new URLs
6. Shut down GCP resources after 1 week of stable operation

---

## Support

For detailed explanations, security best practices, and advanced configuration, see:
- `SELF_HOSTED_MIGRATION_PLAN.md` - Complete migration guide
- `DEPLOYMENT.md` - Original GCP deployment documentation

**Estimated Total Setup Time:** 2-3 hours for experienced admins

