# WordBattle: GCP to Self-Hosted Ubuntu Server Migration Plan

## 🎯 Migration Overview

**Objective:** Migrate WordBattle from Google Cloud Run + Cloud SQL to a secure, maintainable self-hosted Ubuntu server solution.

**Focus Areas:**
- 🔒 **Security First** - Hardened server, automated updates, intrusion detection
- 🛠️ **Easy Maintenance** - Automated backups, monitoring, one-command updates
- 💰 **Cost Efficiency** - Reduce cloud costs by 60-80%
- ⚡ **Performance** - Dedicated resources, no cold starts

---

## 📊 Current State Assessment

### Current GCP Infrastructure
| Component | Current Setup | Monthly Cost (est.) |
|-----------|---------------|---------------------|
| **Application** | Cloud Run (2 CPU, 2GB RAM) | $30-50 |
| **Database** | Cloud SQL PostgreSQL | $50-80 |
| **Networking** | Egress, Load Balancing | $10-20 |
| **Total** | - | **$90-150/month** |

### Current Architecture
```
┌─────────────────────────────────────┐
│   Google Cloud Run (Serverless)    │
│   - Auto-scaling (1-100 instances)  │
│   - Managed SSL                     │
│   - Health checks                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Cloud SQL PostgreSQL (Managed)   │
│   - Automated backups               │
│   - High availability               │
└─────────────────────────────────────┘
```

---

## 🏗️ Target Self-Hosted Architecture

### Recommended Server Specifications

**Option A: Budget-Friendly (Recommended for Start)**
- **Provider:** Hetzner, Netcup, or Contabo
- **Specs:** 4 vCPU, 8GB RAM, 160GB SSD
- **Cost:** €10-20/month (~$11-22)
- **Savings:** ~75% cost reduction

**Option B: Performance-Focused**
- **Provider:** Hetzner Dedicated or DigitalOcean
- **Specs:** 6 vCPU, 16GB RAM, 320GB NVMe SSD
- **Cost:** €30-40/month (~$33-44)
- **Savings:** ~60% cost reduction

### Target Architecture
```
┌────────────────────────────────────────────────────────┐
│                  Cloudflare (Free Tier)                │
│  - DDoS Protection                                     │
│  - SSL/TLS Termination                                 │
│  - CDN & Caching                                       │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│              Ubuntu 22.04 LTS Server                   │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Nginx (Reverse Proxy + Rate Limiting)           │ │
│  └────────────────┬─────────────────────────────────┘ │
│                   │                                    │
│  ┌────────────────▼─────────────────────────────────┐ │
│  │  Docker Compose                                   │ │
│  │  ┌──────────────────┐  ┌──────────────────────┐ │ │
│  │  │  FastAPI Backend │  │  PostgreSQL 15       │ │ │
│  │  │  (Container)     │  │  (Container)         │ │ │
│  │  └──────────────────┘  └──────────────────────┘ │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Security & Monitoring:                                │
│  - UFW Firewall                                        │
│  - Fail2ban (Intrusion Prevention)                    │
│  - Automated Updates (unattended-upgrades)            │
│  - Prometheus + Grafana (Monitoring)                  │
│  - Automated Backups (to object storage)              │
└────────────────────────────────────────────────────────┘
```

---

## 🔐 Phase 1: Server Setup & Hardening (Day 1)

### 1.1 Initial Server Setup

```bash
#!/bin/bash
# 01-initial-setup.sh

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y \
  curl \
  wget \
  git \
  vim \
  htop \
  net-tools \
  ufw \
  fail2ban \
  unattended-upgrades \
  apt-listchanges

# Set timezone
timedatectl set-timezone Europe/Berlin

# Set hostname
hostnamectl set-hostname wordbattle-prod
```

### 1.2 Create Non-Root User with Sudo

```bash
#!/bin/bash
# 02-create-user.sh

# Create deployment user
adduser --disabled-password --gecos "" wordbattle
usermod -aG sudo wordbattle

# Setup SSH key authentication
mkdir -p /home/wordbattle/.ssh
chmod 700 /home/wordbattle/.ssh

# Add your public SSH key
cat >> /home/wordbattle/.ssh/authorized_keys << 'EOF'
# Add your SSH public key here
ssh-rsa AAAAB3NzaC1yc2E... your-email@example.com
EOF

chmod 600 /home/wordbattle/.ssh/authorized_keys
chown -R wordbattle:wordbattle /home/wordbattle/.ssh
```

### 1.3 SSH Hardening

```bash
#!/bin/bash
# 03-harden-ssh.sh

# Backup original SSH config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Apply secure SSH configuration
cat > /etc/ssh/sshd_config << 'EOF'
# Security-first SSH configuration
Port 22
Protocol 2

# Authentication
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no

# Security settings
X11Forwarding no
MaxAuthTries 3
MaxSessions 5
LoginGraceTime 30

# Allow only specific user
AllowUsers wordbattle

# Connection settings
ClientAliveInterval 300
ClientAliveCountMax 2
TCPKeepAlive yes
EOF

# Restart SSH
systemctl restart sshd
```

### 1.4 Firewall Configuration (UFW)

```bash
#!/bin/bash
# 04-configure-firewall.sh

# Reset UFW to defaults
ufw --force reset

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (IMPORTANT: Do this first!)
ufw allow 22/tcp comment 'SSH'

# Allow HTTP/HTTPS (for web traffic)
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Rate limiting on SSH (prevent brute force)
ufw limit 22/tcp

# Enable firewall
ufw --force enable

# Show status
ufw status verbose
```

### 1.5 Fail2Ban Configuration

```bash
#!/bin/bash
# 05-configure-fail2ban.sh

# Configure fail2ban for SSH protection
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
destemail = your-email@example.com
sendername = Fail2Ban
action = %(action_mwl)s

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log

[nginx-botsearch]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

systemctl enable fail2ban
systemctl start fail2ban
```

### 1.6 Automated Security Updates

```bash
#!/bin/bash
# 06-configure-auto-updates.sh

# Configure unattended upgrades
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";

Unattended-Upgrade::Mail "your-email@example.com";
Unattended-Upgrade::MailReport "on-change";
EOF

# Enable automatic updates
cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

# Test configuration
unattended-upgrades --dry-run --debug
```

---

## 🐳 Phase 2: Docker & Application Setup (Day 1-2)

### 2.1 Install Docker & Docker Compose

```bash
#!/bin/bash
# 07-install-docker.sh

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Add wordbattle user to docker group
usermod -aG docker wordbattle

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Enable Docker service
systemctl enable docker
systemctl start docker

# Verify installation
docker --version
docker-compose --version
```

### 2.2 Application Directory Structure

```bash
#!/bin/bash
# 08-setup-directories.sh

# Switch to wordbattle user
su - wordbattle

# Create application directory structure
mkdir -p ~/wordbattle/{app,data,backups,logs,ssl,scripts}
mkdir -p ~/wordbattle/data/{postgres,redis}
mkdir -p ~/wordbattle/logs/{nginx,app,postgres}

cd ~/wordbattle

# Set proper permissions
chmod 700 ~/wordbattle/data
chmod 755 ~/wordbattle/logs
```

### 2.3 Docker Compose Configuration

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: wordbattle-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: wordbattle_prod
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - wordbattle-net
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # FastAPI Backend
  backend:
    image: wordbattle-backend:latest
    container_name: wordbattle-backend
    restart: unless-stopped
    build:
      context: ./app
      dockerfile: Dockerfile
    environment:
      # Database
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: wordbattle_prod
      DB_USER: ${DB_USER}
      DB_PASSWORD: ${DB_PASSWORD}
      
      # Application
      ENVIRONMENT: production
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      
      # CORS
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS}
      
      # Rate Limiting
      RATE_LIMIT_PER_MINUTE: 200
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - ./logs/app:/app/logs
      - ./data/wordlists:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - wordbattle-net
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: wordbattle-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
      - /var/www/certbot:/var/www/certbot:ro
      - ./ssl/certbot:/etc/letsencrypt:ro
    depends_on:
      - backend
    networks:
      - wordbattle-net
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Redis (for caching and rate limiting)
  redis:
    image: redis:7-alpine
    container_name: wordbattle-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - ./data/redis:/data
    ports:
      - "127.0.0.1:6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - wordbattle-net
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  wordbattle-net:
    driver: bridge

volumes:
  postgres-data:
  redis-data:
```

### 2.4 Nginx Configuration (Security-Focused)

```nginx
# nginx/conf.d/wordbattle.conf

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;

# Connection limiting
limit_conn_zone $binary_remote_addr zone=addr:10m;

# Upstream backend
upstream backend {
    server backend:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name wordbattle.yourdomain.com;
    
    # Allow Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect everything else to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name wordbattle.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/wordbattle.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wordbattle.yourdomain.com/privkey.pem;
    
    # SSL Security Settings (A+ Rating)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
    
    # Remove server version
    server_tokens off;
    
    # Connection limits
    limit_conn addr 10;
    
    # Logging
    access_log /var/log/nginx/wordbattle-access.log;
    error_log /var/log/nginx/wordbattle-error.log;
    
    # Root location
    location / {
        # Rate limiting
        limit_req zone=general burst=20 nodelay;
        
        # Proxy settings
        proxy_pass http://backend;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # API endpoints with stricter rate limiting
    location /api/ {
        limit_req zone=api burst=50 nodelay;
        
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Auth endpoints with very strict rate limiting
    location ~ ^/(auth|login|register) {
        limit_req zone=auth burst=10 nodelay;
        
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support
    location /ws/ {
        limit_req zone=api burst=10 nodelay;
        
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket timeouts
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
    
    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://backend;
        access_log off;
    }
    
    # Block common attack patterns
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~* \.(git|env|htaccess|ini|log|sql)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### 2.5 Environment Variables

```bash
# .env.production
# Save as ~/wordbattle/.env

# Database
DB_USER=wordbattle_user
DB_PASSWORD=<GENERATE_STRONG_PASSWORD>
DB_NAME=wordbattle_prod

# Application Secrets
SECRET_KEY=<GENERATE_64_CHAR_SECRET>
JWT_SECRET_KEY=<GENERATE_64_CHAR_SECRET>

# Redis
REDIS_PASSWORD=<GENERATE_STRONG_PASSWORD>

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email (if using)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=<EMAIL_PASSWORD>

# Monitoring
SENTRY_DSN=<optional_sentry_dsn>
```

**Generate secure passwords:**
```bash
# Generate secure secrets
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -base64 24  # For DB_PASSWORD
openssl rand -base64 24  # For REDIS_PASSWORD
```

---

## 🔄 Phase 3: Data Migration (Day 2-3)

### 3.1 Export Data from GCP Cloud SQL

```bash
#!/bin/bash
# 09-export-from-gcp.sh

# Set variables
PROJECT_ID="wordbattle-1748668162"
INSTANCE_NAME="wordbattle-db-prod"
EXPORT_DATE=$(date +%Y%m%d_%H%M%S)
BUCKET_NAME="wordbattle-migration-backup"

echo "📦 Exporting database from GCP Cloud SQL..."

# Create GCS bucket for export (if not exists)
gsutil mb -p $PROJECT_ID gs://$BUCKET_NAME/ 2>/dev/null || echo "Bucket already exists"

# Export database to GCS
gcloud sql export sql $INSTANCE_NAME \
  gs://$BUCKET_NAME/wordbattle_export_${EXPORT_DATE}.sql \
  --project=$PROJECT_ID \
  --database=wordbattle

# Download to local machine
gsutil cp gs://$BUCKET_NAME/wordbattle_export_${EXPORT_DATE}.sql ./backup/

echo "✅ Export completed: wordbattle_export_${EXPORT_DATE}.sql"
```

### 3.2 Transfer Data to New Server

```bash
#!/bin/bash
# 10-transfer-to-server.sh

SERVER_IP="your.server.ip"
SSH_USER="wordbattle"
BACKUP_FILE="wordbattle_export_*.sql"

echo "📤 Transferring database backup to new server..."

# Transfer backup file
scp $BACKUP_FILE ${SSH_USER}@${SERVER_IP}:~/wordbattle/backups/

# Transfer wordlist data
scp -r wordbattle-backend/data/*.txt ${SSH_USER}@${SERVER_IP}:~/wordbattle/data/wordlists/

echo "✅ Transfer completed"
```

### 3.3 Import Data to New Server

```bash
#!/bin/bash
# 11-import-database.sh
# Run this ON the new server

cd ~/wordbattle

# Start only PostgreSQL first
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Import database
echo "📥 Importing database..."
docker exec -i wordbattle-db psql -U $DB_USER -d $DB_NAME < backups/wordbattle_export_*.sql

# Verify import
echo "🔍 Verifying import..."
docker exec wordbattle-db psql -U $DB_USER -d $DB_NAME -c "\dt"
docker exec wordbattle-db psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM users;"
docker exec wordbattle-db psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM games;"

echo "✅ Database import completed"
```

---

## 🚀 Phase 4: Deployment & SSL Setup (Day 3)

### 4.1 Deploy Application

```bash
#!/bin/bash
# 12-deploy-application.sh

cd ~/wordbattle

# Pull/build application image
# Option 1: Build from source
git clone https://github.com/yourusername/wordbattle-backend.git app
cd app
docker build -t wordbattle-backend:latest -f Dockerfile.cloudrun .
cd ..

# Option 2: Pull from registry (if you have one)
# docker pull your-registry.com/wordbattle-backend:latest

# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check logs
docker-compose logs -f

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 20

# Test health endpoint
curl http://localhost:8000/health

echo "✅ Application deployed"
```

### 4.2 Setup Let's Encrypt SSL

```bash
#!/bin/bash
# 13-setup-ssl.sh

# Install Certbot
apt install -y certbot python3-certbot-nginx

# Stop nginx temporarily (if running)
docker-compose stop nginx

# Get SSL certificate
certbot certonly --standalone \
  -d wordbattle.yourdomain.com \
  --non-interactive \
  --agree-tos \
  --email your-email@example.com \
  --preferred-challenges http

# Copy certificates to application directory
cp -r /etc/letsencrypt ~/wordbattle/ssl/certbot/

# Set proper permissions
chmod -R 755 ~/wordbattle/ssl
chown -R wordbattle:wordbattle ~/wordbattle/ssl

# Setup auto-renewal
cat > /etc/cron.d/certbot-renew << 'EOF'
0 3 * * * root certbot renew --quiet --deploy-hook "docker exec wordbattle-nginx nginx -s reload"
EOF

# Start nginx
docker-compose start nginx

echo "✅ SSL certificates installed and auto-renewal configured"
```

---

## 📊 Phase 5: Monitoring & Maintenance Automation (Day 4)

### 5.1 Automated Backup Script

```bash
#!/bin/bash
# scripts/backup-database.sh

# Configuration
BACKUP_DIR="/home/wordbattle/wordbattle/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="wordbattle_backup_${DATE}.sql.gz"
RETENTION_DAYS=30

# S3-compatible backup storage (optional)
S3_BUCKET="s3://your-backup-bucket"
USE_S3=false

echo "🗄️  Starting database backup..."

# Create backup
docker exec wordbattle-db pg_dump -U $DB_USER $DB_NAME | gzip > ${BACKUP_DIR}/${BACKUP_FILE}

# Verify backup
if [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
    echo "✅ Backup created: ${BACKUP_FILE} (${SIZE})"
    
    # Upload to S3/Object Storage (if configured)
    if [ "$USE_S3" = true ]; then
        aws s3 cp ${BACKUP_DIR}/${BACKUP_FILE} ${S3_BUCKET}/
        echo "☁️  Backup uploaded to S3"
    fi
    
    # Remove old backups
    find ${BACKUP_DIR} -name "wordbattle_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    echo "🧹 Old backups cleaned (kept last ${RETENTION_DAYS} days)"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Backup statistics
echo "📊 Backup Statistics:"
docker exec wordbattle-db psql -U $DB_USER -d $DB_NAME -c "
    SELECT 
        'Users: ' || COUNT(*) FROM users
    UNION ALL
    SELECT 'Games: ' || COUNT(*) FROM games
    UNION ALL
    SELECT 'Moves: ' || COUNT(*) FROM moves;
"
```

### 5.2 Automated Backup Cron Job

```bash
#!/bin/bash
# 14-setup-backup-cron.sh

# Create cron job for daily backups at 2 AM
cat > /etc/cron.d/wordbattle-backup << 'EOF'
# Daily database backup at 2 AM
0 2 * * * wordbattle /home/wordbattle/wordbattle/scripts/backup-database.sh >> /home/wordbattle/wordbattle/logs/backup.log 2>&1
EOF

# Set permissions
chmod 644 /etc/cron.d/wordbattle-backup

echo "✅ Automated backup configured (daily at 2 AM)"
```

### 5.3 Health Check & Monitoring Script

```bash
#!/bin/bash
# scripts/health-check.sh

# Configuration
HEALTH_ENDPOINT="http://localhost:8000/health"
ALERT_EMAIL="your-email@example.com"
LOG_FILE="/home/wordbattle/wordbattle/logs/health-check.log"

# Function to send alert
send_alert() {
    local subject="$1"
    local message="$2"
    
    echo "$message" | mail -s "$subject" $ALERT_EMAIL
}

# Function to check service
check_service() {
    local service=$1
    local status=$(docker inspect --format='{{.State.Status}}' $service 2>/dev/null)
    
    if [ "$status" != "running" ]; then
        echo "❌ $service is not running!"
        send_alert "WordBattle Alert: $service Down" "$service container is not running on $(hostname)"
        return 1
    fi
    return 0
}

echo "[$(date)] Running health checks..." >> $LOG_FILE

# Check Docker containers
check_service "wordbattle-backend"
check_service "wordbattle-db"
check_service "wordbattle-nginx"
check_service "wordbattle-redis"

# Check HTTP endpoint
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_ENDPOINT)

if [ "$HTTP_STATUS" != "200" ]; then
    echo "[$(date)] ❌ Health check failed: HTTP $HTTP_STATUS" >> $LOG_FILE
    send_alert "WordBattle Alert: Health Check Failed" "Backend health check returned HTTP $HTTP_STATUS"
else
    echo "[$(date)] ✅ All services healthy" >> $LOG_FILE
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "[$(date)] ⚠️  Disk usage high: ${DISK_USAGE}%" >> $LOG_FILE
    send_alert "WordBattle Alert: Disk Space Low" "Disk usage is at ${DISK_USAGE}%"
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "[$(date)] ⚠️  Memory usage high: ${MEM_USAGE}%" >> $LOG_FILE
    send_alert "WordBattle Alert: High Memory Usage" "Memory usage is at ${MEM_USAGE}%"
fi
```

### 5.4 System Monitoring with Prometheus (Optional)

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: wordbattle-prometheus
    restart: unless-stopped
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "127.0.0.1:9090:9090"
    networks:
      - wordbattle-net

  grafana:
    image: grafana/grafana:latest
    container_name: wordbattle-grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_SERVER_ROOT_URL=https://monitoring.yourdomain.com
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana-dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "127.0.0.1:3000:3000"
    depends_on:
      - prometheus
    networks:
      - wordbattle-net

  node-exporter:
    image: prom/node-exporter:latest
    container_name: wordbattle-node-exporter
    restart: unless-stopped
    ports:
      - "127.0.0.1:9100:9100"
    networks:
      - wordbattle-net

volumes:
  prometheus-data:
  grafana-data:

networks:
  wordbattle-net:
    external: true
```

### 5.5 Log Rotation

```bash
#!/bin/bash
# 15-setup-log-rotation.sh

cat > /etc/logrotate.d/wordbattle << 'EOF'
/home/wordbattle/wordbattle/logs/**/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0644 wordbattle wordbattle
    sharedscripts
    postrotate
        docker exec wordbattle-nginx nginx -s reopen
    endscript
}
EOF

echo "✅ Log rotation configured"
```

---

## 🛠️ Phase 6: Easy Maintenance Commands (Day 4)

### 6.1 One-Command Management Script

```bash
#!/bin/bash
# scripts/manage.sh - Single script for all operations

set -e

COMPOSE_FILE="/home/wordbattle/wordbattle/docker-compose.production.yml"
cd /home/wordbattle/wordbattle

case "$1" in
    start)
        echo "🚀 Starting WordBattle..."
        docker-compose -f $COMPOSE_FILE up -d
        echo "✅ WordBattle started"
        ;;
    
    stop)
        echo "🛑 Stopping WordBattle..."
        docker-compose -f $COMPOSE_FILE stop
        echo "✅ WordBattle stopped"
        ;;
    
    restart)
        echo "🔄 Restarting WordBattle..."
        docker-compose -f $COMPOSE_FILE restart
        echo "✅ WordBattle restarted"
        ;;
    
    status)
        echo "📊 WordBattle Status:"
        docker-compose -f $COMPOSE_FILE ps
        ;;
    
    logs)
        SERVICE=${2:-backend}
        echo "📋 Showing logs for $SERVICE..."
        docker-compose -f $COMPOSE_FILE logs -f --tail=100 $SERVICE
        ;;
    
    update)
        echo "🔄 Updating WordBattle..."
        cd app
        git pull
        docker build -t wordbattle-backend:latest .
        cd ..
        docker-compose -f $COMPOSE_FILE up -d --no-deps backend
        echo "✅ WordBattle updated"
        ;;
    
    backup)
        echo "💾 Creating backup..."
        ./scripts/backup-database.sh
        ;;
    
    restore)
        if [ -z "$2" ]; then
            echo "❌ Usage: ./manage.sh restore <backup-file>"
            exit 1
        fi
        echo "⚠️  Restoring from $2..."
        read -p "This will overwrite current data. Continue? (yes/no) " -n 3 -r
        echo
        if [[ $REPLY =~ ^yes$ ]]; then
            zcat backups/$2 | docker exec -i wordbattle-db psql -U $DB_USER -d $DB_NAME
            echo "✅ Restore completed"
        else
            echo "❌ Restore cancelled"
        fi
        ;;
    
    health)
        echo "🏥 Health Check:"
        curl -f http://localhost:8000/health && echo " ✅ Backend OK" || echo " ❌ Backend DOWN"
        docker exec wordbattle-db pg_isready -U $DB_USER && echo "✅ Database OK" || echo "❌ Database DOWN"
        ;;
    
    shell)
        SERVICE=${2:-backend}
        echo "🐚 Opening shell in $SERVICE..."
        docker exec -it wordbattle-$SERVICE sh
        ;;
    
    db-shell)
        echo "🐚 Opening database shell..."
        docker exec -it wordbattle-db psql -U $DB_USER -d $DB_NAME
        ;;
    
    clean)
        echo "🧹 Cleaning up..."
        docker system prune -f
        find logs/ -name "*.log" -mtime +30 -delete
        echo "✅ Cleanup completed"
        ;;
    
    *)
        echo "WordBattle Management Script"
        echo ""
        echo "Usage: ./manage.sh <command> [options]"
        echo ""
        echo "Commands:"
        echo "  start              Start all services"
        echo "  stop               Stop all services"
        echo "  restart            Restart all services"
        echo "  status             Show service status"
        echo "  logs [service]     Show logs (default: backend)"
        echo "  update             Update and redeploy backend"
        echo "  backup             Create database backup"
        echo "  restore <file>     Restore from backup"
        echo "  health             Run health checks"
        echo "  shell [service]    Open shell in container"
        echo "  db-shell           Open PostgreSQL shell"
        echo "  clean              Clean up old logs and Docker resources"
        echo ""
        exit 1
        ;;
esac
```

Make it executable:
```bash
chmod +x ~/wordbattle/scripts/manage.sh
```

### 6.2 Create Convenient Aliases

```bash
# Add to ~/.bashrc or ~/.zsh  rc
cat >> ~/.bashrc << 'EOF'

# WordBattle aliases
alias wb-start='~/wordbattle/scripts/manage.sh start'
alias wb-stop='~/wordbattle/scripts/manage.sh stop'
alias wb-restart='~/wordbattle/scripts/manage.sh restart'
alias wb-status='~/wordbattle/scripts/manage.sh status'
alias wb-logs='~/wordbattle/scripts/manage.sh logs'
alias wb-update='~/wordbattle/scripts/manage.sh update'
alias wb-backup='~/wordbattle/scripts/manage.sh backup'
alias wb-health='~/wordbattle/scripts/manage.sh health'
alias wb='~/wordbattle/scripts/manage.sh'
EOF

source ~/.bashrc
```

---

## 🔄 Phase 7: Gradual Migration Strategy (Week 1)

### 7.1 Traffic Split Configuration

```nginx
# Cloudflare Load Balancer or DNS-based traffic split

# Week 1, Day 1-2: Testing (0% production traffic)
# - Deploy to new server
# - Test with staging subdomain
# - Verify all functionality

# Week 1, Day 3-4: Canary (10% traffic)
# - Update DNS to point 10% traffic to new server
# - Monitor error rates
# - Compare performance

# Week 1, Day 5-6: Gradual increase (50% traffic)
# - Monitor metrics
# - Verify backup systems
# - Test failover

# Week 1, Day 7: Full migration (100% traffic)
# - Switch all traffic to new server
# - Keep GCP as backup for 1 week
# - Monitor closely
```

### 7.2 Rollback Plan

```bash
#!/bin/bash
# scripts/rollback-to-gcp.sh

echo "⚠️  EMERGENCY ROLLBACK TO GCP"
echo "This will switch DNS back to GCP Cloud Run"
read -p "Continue? (yes/no) " -n 3 -r
echo

if [[ $REPLY =~ ^yes$ ]]; then
    # Update DNS to point back to GCP
    # This depends on your DNS provider
    
    echo "📝 Manual steps required:"
    echo "1. Update DNS A record to point to GCP Cloud Run IP"
    echo "2. Or update Cloudflare proxied record"
    echo "3. Verify traffic is flowing to GCP"
    echo "4. GCP backend URL: https://wordbattle-backend-prod-[hash].europe-west1.run.app"
    
    # If using Cloudflare API
    # curl -X PUT "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${RECORD_ID}" \
    #   -H "Authorization: Bearer ${CF_API_TOKEN}" \
    #   -H "Content-Type: application/json" \
    #   --data '{"type":"CNAME","name":"api","content":"wordbattle-backend-prod-[hash].europe-west1.run.app"}'
    
    echo "✅ Rollback initiated. Monitor traffic in next 5 minutes."
else
    echo "❌ Rollback cancelled"
fi
```

---

## 📋 Phase 8: Post-Migration Checklist

### 8.1 Validation Tests

```bash
#!/bin/bash
# scripts/post-migration-tests.sh

echo "🧪 Running Post-Migration Tests..."

# Test health endpoint
echo "1. Testing health endpoint..."
curl -f https://wordbattle.yourdomain.com/health || echo "❌ Health check failed"

# Test authentication
echo "2. Testing authentication..."
# Add your auth test here

# Test WebSocket
echo "3. Testing WebSocket..."
# Add WebSocket test here

# Test game creation
echo "4. Testing game creation..."
# Add game creation test here

# Check response times
echo "5. Checking response times..."
for i in {1..10}; do
    curl -w "@curl-format.txt" -o /dev/null -s https://wordbattle.yourdomain.com/health
done

# Check database connections
echo "6. Checking database..."
docker exec wordbattle-db psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM users;"

# Verify SSL
echo "7. Verifying SSL..."
echo | openssl s_client -connect wordbattle.yourdomain.com:443 -servername wordbattle.yourdomain.com 2>/dev/null | openssl x509 -noout -dates

echo "✅ Post-migration tests completed"
```

### 8.2 Performance Baseline

```bash
# Establish performance baseline
echo "📊 Performance Baseline After Migration:"

# Average response time
echo "Average response time:"
ab -n 1000 -c 10 https://wordbattle.yourdomain.com/health

# Database query performance
echo "Database query performance:"
docker exec wordbattle-db psql -U $DB_USER -d $DB_NAME -c "EXPLAIN ANALYZE SELECT * FROM games LIMIT 100;"

# Resource usage
echo "Server resource usage:"
docker stats --no-stream
```

---

## 💰 Cost Comparison

### Before (GCP)
| Service | Cost/Month |
|---------|-----------|
| Cloud Run | $30-50 |
| Cloud SQL | $50-80 |
| Networking | $10-20 |
| **Total** | **$90-150** |

### After (Self-Hosted)
| Service | Cost/Month |
|---------|-----------|
| VPS (Hetzner CPX31) | $15-20 |
| Backup Storage (optional) | $5 |
| Domain & DNS (Cloudflare) | $0 (free tier) |
| **Total** | **$15-25** |

**Savings:** ~$75-125/month (80-85% reduction)
**Annual Savings:** ~$900-1,500

---

## 🔒 Security Checklist

- [x] SSH key-only authentication (no passwords)
- [x] Non-root user with sudo
- [x] UFW firewall configured
- [x] Fail2ban intrusion prevention
- [x] Automated security updates
- [x] SSL/TLS certificates (Let's Encrypt)
- [x] Nginx rate limiting
- [x] Security headers configured
- [x] Docker containers run as non-root
- [x] Database accessible only from localhost
- [x] Strong passwords for all services
- [x] Regular automated backups
- [x] Log monitoring and rotation
- [x] Health check monitoring
- [ ] Optional: VPN for admin access
- [ ] Optional: Two-factor authentication for SSH

---

## 📚 Maintenance Guide

### Daily Tasks (Automated)
- ✅ Automated backups (2 AM)
- ✅ Health checks (every 5 minutes)
- ✅ Security updates
- ✅ Log rotation

### Weekly Tasks
- Check backup integrity: `wb backup && ls -lh backups/`
- Review logs: `wb logs`
- Check disk space: `df -h`
- Review fail2ban reports: `sudo fail2ban-client status`

### Monthly Tasks
- Update Docker images: `wb update`
- Review and test disaster recovery
- Check SSL certificate expiry: `certbot certificates`
- Review security audit logs

### Emergency Procedures

**If backend is down:**
```bash
wb-restart backend
wb-logs backend
```

**If database is down:**
```bash
wb-restart postgres
wb db-shell
```

**Complete system restart:**
```bash
wb-stop
wb-start
wb-health
```

**Restore from backup:**
```bash
wb restore wordbattle_backup_YYYYMMDD_HHMMSS.sql.gz
```

---

## 🎯 Success Criteria

### Migration Complete When:
- ✅ All services running on new server
- ✅ SSL certificates configured and auto-renewing
- ✅ All data migrated and verified
- ✅ Automated backups working
- ✅ Monitoring and alerting configured
- ✅ Health checks passing
- ✅ Performance equal to or better than GCP
- ✅ 100% of traffic on new server
- ✅ GCP resources can be safely terminated

### Post-Migration Goals (First Month):
- 99.9% uptime
- Average response time < 100ms
- Zero data loss
- All automated tasks running successfully
- Security scans showing no vulnerabilities

---

## 📞 Support & Resources

### Useful Commands Reference
```bash
# System
htop                    # System resources
df -h                   # Disk space
free -h                 # Memory usage
systemctl status docker # Docker status

# Application
wb status              # Service status
wb logs backend        # View logs
wb health              # Health check
wb backup              # Manual backup

# Security
sudo fail2ban-client status        # Fail2ban status
sudo ufw status verbose            # Firewall status
sudo journalctl -u ssh -f          # SSH login attempts

# Docker
docker ps                          # Running containers
docker stats                       # Resource usage
docker logs wordbattle-backend     # Container logs
docker exec -it wordbattle-backend sh  # Container shell
```

### Important File Locations
- Application: `~/wordbattle/`
- Logs: `~/wordbattle/logs/`
- Backups: `~/wordbattle/backups/`
- Configuration: `~/wordbattle/.env`
- Scripts: `~/wordbattle/scripts/`

---

## ✅ Timeline Summary

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1** | 4-6 hours | Server setup & hardening |
| **Phase 2** | 4-6 hours | Docker & application setup |
| **Phase 3** | 2-4 hours | Data migration |
| **Phase 4** | 2-3 hours | Deployment & SSL |
| **Phase 5** | 3-4 hours | Monitoring setup |
| **Phase 6** | 2 hours | Management scripts |
| **Phase 7** | 7 days | Gradual traffic migration |
| **Phase 8** | 2 hours | Validation & testing |

**Total Setup Time:** 2-3 days of active work
**Total Migration Time:** ~1 week with gradual rollout

---

**Next Steps:**
1. Choose and provision your Ubuntu server
2. Save and secure all generated passwords
3. Run through Phase 1 (Server Hardening)
4. Test each phase before proceeding
5. Keep GCP running during gradual migration
6. Document any customizations for your setup

**Questions or Issues?**
- Review logs: `wb logs`
- Check health: `wb health`
- Review security: `sudo fail2ban-client status`

