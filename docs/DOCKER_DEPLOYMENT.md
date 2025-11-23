# Docker Compose Production Deployment

Comprehensive guide for deploying the Agentic Platform using Docker Compose in production environments.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Server Setup](#server-setup)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Secrets Management](#secrets-management)
- [Initial Deployment](#initial-deployment)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Post-Deployment](#post-deployment)
- [Monitoring](#monitoring)
- [Backups](#backups)
- [Updates](#updates)
- [Troubleshooting](#troubleshooting)

## Overview

This production deployment uses:
- **Docker Compose** for container orchestration
- **Nginx** as reverse proxy with HTTPS termination
- **PostgreSQL** (with pgvector) for database
- **Redis** for caching
- **Automated backups** to local storage and S3
- **Prometheus/Grafana** for monitoring (optional)
- **Sentry** for error tracking (optional)

**Best for:**
- Single-server deployments
- Small to medium scale (< 10K users)
- Development, staging, and small production environments

**Not recommended for:**
- Multi-region deployments
- High-availability requirements
- Extreme scale (use Kubernetes instead)

## Prerequisites

### Hardware Requirements

**Minimum:**
- 2 CPU cores
- 4 GB RAM
- 50 GB SSD storage

**Recommended:**
- 4+ CPU cores
- 8+ GB RAM
- 100+ GB SSD storage

### Software Requirements

- **OS:** Ubuntu 22.04 LTS (recommended) or similar Linux distribution
- **Docker:** 24.0.0 or later
- **Docker Compose:** 2.20.0 or later
- **Git:** For cloning the repository

### Network Requirements

- **Static IP address**
- **Domain name** pointing to your server
- **Open ports:**
  - 80 (HTTP)
  - 443 (HTTPS)
  - 22 (SSH, restricted to your IPs)

### DNS Setup

Point your domain to the server:

```bash
# A record
api.yourdomain.com -> your.server.ip.address

# Verify DNS propagation
dig api.yourdomain.com
nslookup api.yourdomain.com
```

## Server Setup

### 1. Update System

```bash
# Update package list and upgrade
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw
```

### 2. Install Docker

```bash
# Install Docker using convenience script
curl -fsSL https://get.docker.com | sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in for group changes
# Verify installation
docker --version
docker compose version
```

### 3. Create Deployment Structure

```bash
# Create deployment directory
sudo mkdir -p /opt/agentic-platform
sudo chown $USER:$USER /opt/agentic-platform
cd /opt/agentic-platform

# Create required subdirectories
mkdir -p {secrets,nginx/ssl,nginx/logs,backups,logs}
```

### 4. Configure Firewall

```bash
# Set up UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Enable firewall
sudo ufw --force enable
sudo ufw status
```

### 5. Clone Repository

```bash
cd /opt/agentic-platform

# Clone repository
git clone https://github.com/your-org/agentic-platform.git .

# Or if using SSH
git clone git@github.com:your-org/agentic-platform.git .
```

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Recommended)

Free SSL certificates with auto-renewal:

```bash
# Install Certbot
sudo apt install -y certbot

# Obtain certificate (replace with your domain)
sudo certbot certonly --standalone \
    -d api.yourdomain.com \
    --agree-tos \
    --email admin@yourdomain.com \
    --non-interactive

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem \
    nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/api.yourdomain.com/privkey.pem \
    nginx/ssl/key.pem

# Set permissions
sudo chown $USER:$USER nginx/ssl/*.pem
chmod 600 nginx/ssl/*.pem
```

**Set up auto-renewal:**

```bash
# Test renewal
sudo certbot renew --dry-run

# Add renewal cron job
sudo crontab -e
# Add this line:
0 0 1 * * certbot renew --quiet --deploy-hook "cp /etc/letsencrypt/live/api.yourdomain.com/*.pem /opt/agentic-platform/nginx/ssl/ && docker-compose -f /opt/agentic-platform/docker-compose.prod.yml restart nginx"
```

### Option 2: Commercial Certificate

If you have a commercial SSL certificate:

```bash
# Copy your certificate files
cp /path/to/certificate.crt nginx/ssl/cert.pem
cp /path/to/private.key nginx/ssl/key.pem
cp /path/to/ca-bundle.crt nginx/ssl/ca-bundle.pem  # If needed

# Secure permissions
chmod 600 nginx/ssl/*.pem
```

### Option 3: Self-Signed (Testing Only)

**Not recommended for production!**

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=api.yourdomain.com"
```

## Secrets Management

### 1. Generate Secrets

```bash
cd /opt/agentic-platform/secrets

# Database credentials
echo "postgres" > db_user.txt
openssl rand -base64 32 > db_password.txt

# Application secrets (minimum 64 characters for production)
openssl rand -base64 64 > secret_key.txt
openssl rand -base64 64 > jwt_secret.txt

# API keys (replace with your actual keys)
echo "sk-ant-your-anthropic-api-key" > anthropic_api_key.txt
echo "sk-your-openai-api-key" > openai_api_key.txt
```

### 2. Secure Secret Files

```bash
# Restrict permissions to owner-only
chmod 600 secrets/*.txt

# Verify permissions
ls -la secrets/
# Should show: -rw------- (600)
```

### 3. Important Security Notes

- **Never commit secrets to version control**
- Add `secrets/*.txt` to `.gitignore`
- Rotate secrets regularly (every 90 days)
- Use different secrets for each environment
- Back up secrets securely (encrypted)

## Configuration

### 1. Environment Variables

Create production environment file:

```bash
cat > .env.prod << 'EOF'
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
VERSION=1.0.0

# Database
DB_PASSWORD=$(cat secrets/db_password.txt)
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_PASSWORD=$(openssl rand -base64 32)
REDIS_POOL_SIZE=10

# CORS (update with your domains)
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true

# Backup Configuration
BACKUP_RETENTION_DAYS=30
# Optional: S3 backup
BACKUP_S3_BUCKET=
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Sentry (optional - for error tracking)
SENTRY_DSN=
EOF

# Secure environment file
chmod 600 .env.prod
```

### 2. Update Nginx Configuration

Edit `nginx/nginx.conf` and update the server_name:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;  # <- Update this

    # Rest of configuration...
}
```

### 3. Update docker-compose.prod.yml

Update any environment-specific values:

```yaml
services:
  api:
    environment:
      ALLOWED_ORIGINS: https://yourdomain.com  # Update
```

## Initial Deployment

### 1. Build Images

```bash
cd /opt/agentic-platform

# Build all images
docker-compose -f docker-compose.prod.yml build

# This may take several minutes on first run
```

### 2. Initialize Database

```bash
# Start database services only
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Wait for database to be ready
sleep 15

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# Verify migrations
docker-compose -f docker-compose.prod.yml run --rm api alembic current
```

### 3. Create Admin User (Optional)

```bash
# You'll need to create this script or do it manually via API
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U postgres -d agentic_db -c \
    "INSERT INTO users (email, hashed_password, is_admin) VALUES ('admin@yourdomain.com', 'hashed_password_here', true);"
```

## Deployment

### 1. Start All Services

```bash
cd /opt/agentic-platform

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View startup logs
docker-compose -f docker-compose.prod.yml logs -f
# Press Ctrl+C to exit logs (services continue running)
```

### 2. Verify Services

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Should show:
# NAME                      STATUS
# agentic-postgres-prod    Up (healthy)
# agentic-redis-prod       Up (healthy)
# agentic-api-prod         Up (healthy)
# agentic-nginx-prod       Up (healthy)
# agentic-backup-prod      Up

# Check individual service health
docker-compose -f docker-compose.prod.yml exec api curl http://localhost:8000/health/ready
```

### 3. Test External Access

```bash
# Test HTTPS endpoint
curl https://api.yourdomain.com/health/ready

# Should return:
# {"status":"ready","database":true}

# Test API documentation
curl https://api.yourdomain.com/docs
# Should return HTML
```

## Post-Deployment

### 1. Set Up System Service

Create systemd service for auto-start on boot:

```bash
sudo tee /etc/systemd/system/agentic-platform.service << 'EOF'
[Unit]
Description=Agentic Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/agentic-platform
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF

# Replace $USER with actual username
sudo sed -i "s/\$USER/$USER/g" /etc/systemd/system/agentic-platform.service

# Enable and start service
sudo systemctl enable agentic-platform
sudo systemctl start agentic-platform

# Check status
sudo systemctl status agentic-platform
```

### 2. Configure Log Rotation

```bash
sudo tee /etc/logrotate.d/agentic-platform << 'EOF'
/opt/agentic-platform/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0640 $USER $USER
    sharedscripts
    postrotate
        docker-compose -f /opt/agentic-platform/docker-compose.prod.yml restart api
    endscript
}

/opt/agentic-platform/nginx/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 0640 $USER $USER
    sharedscripts
    postrotate
        docker-compose -f /opt/agentic-platform/docker-compose.prod.yml restart nginx
    endscript
}
EOF

# Replace $USER
sudo sed -i "s/\$USER/$USER/g" /etc/logrotate.d/agentic-platform

# Test rotation
sudo logrotate -d /etc/logrotate.d/agentic-platform
```

### 3. Set Up Monitoring (Optional)

#### Start Observability Stack

```bash
# Start Prometheus, Grafana, Jaeger
docker-compose -f docker-compose.observability.yml up -d

# Access Grafana (default: admin/admin)
# http://your-server-ip:3000

# Import dashboards from observability/grafana/dashboards/
```

#### Configure Sentry

```bash
# Add Sentry DSN to .env.prod
echo "SENTRY_DSN=https://your-sentry-dsn@sentry.io/project" >> .env.prod

# Restart API
docker-compose -f docker-compose.prod.yml restart api
```

## Monitoring

### Health Checks

```bash
# Liveness check
curl https://api.yourdomain.com/health/live

# Readiness check (includes DB connectivity)
curl https://api.yourdomain.com/health/ready

# Pretty-print JSON
curl https://api.yourdomain.com/health/ready | jq .
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs

# Specific service
docker-compose -f docker-compose.prod.yml logs api
docker-compose -f docker-compose.prod.yml logs nginx

# Follow logs (real-time)
docker-compose -f docker-compose.prod.yml logs -f api

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 api

# Search logs
docker-compose -f docker-compose.prod.yml logs api | grep ERROR
```

### Metrics

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# View in browser (requires port forwarding or internal access)
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

### Service Status

```bash
# Docker Compose status
docker-compose -f docker-compose.prod.yml ps

# Individual service status
docker-compose -f docker-compose.prod.yml ps api

# Resource usage
docker stats

# Disk usage
docker system df
```

## Backups

Backups run automatically via the backup service.

### Configuration

Default schedule: **Daily at 2 AM UTC**

Modify in `docker-compose.prod.yml`:

```yaml
backup:
  environment:
    BACKUP_SCHEDULE: "0 2 * * *"  # Cron format
    BACKUP_RETENTION_DAYS: 30
```

### Manual Backup

```bash
# Run manual backup
docker-compose -f docker-compose.prod.yml exec backup /usr/local/bin/backup.sh

# View backup logs
docker-compose -f docker-compose.prod.yml logs backup

# List backups
ls -lh backups/
```

### Verify Backups

```bash
# Check latest backup exists
ls -lt backups/backup_agentic_db_*.sql.gz | head -1

# Verify checksum
cd backups
sha256sum -c $(ls -t backup_*.sha256 | head -1)
```

### Restore from Backup

```bash
# 1. Stop API service
docker-compose -f docker-compose.prod.yml stop api

# 2. Choose backup file
BACKUP_FILE=backups/backup_agentic_db_20250122_020015.sql.gz

# 3. Verify checksum
sha256sum -c ${BACKUP_FILE}.sha256

# 4. Restore
gunzip -c ${BACKUP_FILE} | \
    docker exec -i agentic-postgres-prod \
    psql -U postgres -d agentic_db

# 5. Restart services
docker-compose -f docker-compose.prod.yml start api

# 6. Verify
curl https://api.yourdomain.com/health/ready
```

### S3 Backup Configuration

For off-site backups:

```bash
# Add to .env.prod
BACKUP_S3_BUCKET=your-backup-bucket
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Restart backup service
docker-compose -f docker-compose.prod.yml restart backup

# Verify S3 upload
aws s3 ls s3://your-backup-bucket/backups/
```

## Updates

### Zero-Downtime Updates

```bash
cd /opt/agentic-platform

# 1. Pull latest code
git pull origin main

# 2. Build new images
docker-compose -f docker-compose.prod.yml build api

# 3. Run database migrations
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# 4. Rolling update (minimal downtime)
docker-compose -f docker-compose.prod.yml up -d --no-deps --build api

# 5. Verify deployment
sleep 10
curl https://api.yourdomain.com/health/ready

# 6. Check logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=50 api
```

### Rollback

If the update fails:

```bash
# 1. Revert code
git checkout previous-working-commit

# 2. Rebuild images
docker-compose -f docker-compose.prod.yml build api

# 3. Restart
docker-compose -f docker-compose.prod.yml up -d

# 4. Rollback database (if needed)
docker-compose -f docker-compose.prod.yml run --rm api alembic downgrade -1

# 5. Verify
curl https://api.yourdomain.com/health/ready
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs <service-name>

# Check Docker daemon
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Remove and recreate
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Database Connection Errors

```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U postgres -d agentic_db -c "SELECT 1;"

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Verify credentials
cat secrets/db_user.txt
cat secrets/db_password.txt

# Restart database
docker-compose -f docker-compose.prod.yml restart postgres
```

### SSL Certificate Errors

```bash
# Verify certificate
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Check expiration
openssl x509 -in nginx/ssl/cert.pem -noout -dates

# Test SSL
openssl s_client -connect api.yourdomain.com:443

# Check nginx config
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### High Memory Usage

```bash
# Check memory usage
docker stats

# Set memory limits in docker-compose.prod.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G

# Restart with limits
docker-compose -f docker-compose.prod.yml up -d
```

### Disk Space Issues

```bash
# Check disk usage
df -h
docker system df

# Clean up
docker system prune -a  # Remove unused images
docker volume prune     # Remove unused volumes

# Clean old logs
find logs/ -name "*.log" -mtime +7 -delete
find nginx/logs/ -name "*.log" -mtime +7 -delete

# Clean old backups
find backups/ -name "*.sql.gz" -mtime +30 -delete
```

## Security Best Practices

1. **Keep secrets secure**
   - Never commit to version control
   - Use strong, unique passwords
   - Rotate regularly

2. **Keep software updated**
   - Update Docker regularly
   - Update base images
   - Apply security patches

3. **Restrict access**
   - Use firewall (UFW)
   - SSH key authentication only
   - Whitelist admin IPs

4. **Monitor logs**
   - Check for unauthorized access
   - Monitor error rates
   - Set up alerts

5. **Regular backups**
   - Test restore procedures
   - Off-site backups (S3)
   - Encrypt sensitive data

6. **Use HTTPS**
   - Valid SSL certificates
   - TLS 1.2 minimum
   - Strong ciphers

## Maintenance Checklist

### Daily
- [ ] Check service health
- [ ] Review error logs
- [ ] Monitor disk space

### Weekly
- [ ] Review security logs
- [ ] Check backup success
- [ ] Review performance metrics

### Monthly
- [ ] Update dependencies
- [ ] Test backup restoration
- [ ] Review access logs
- [ ] Security scan

### Quarterly
- [ ] Rotate secrets
- [ ] Update SSL certificates (if not auto-renewing)
- [ ] Review and update documentation
- [ ] Disaster recovery test

## Additional Resources

- [Operations Runbook](./RUNBOOK.md)
- [Observability Guide](./OBSERVABILITY.md)
- [Sentry Documentation](./SENTRY.md)
- [Performance Guide](./PERFORMANCE.md)
- [Backup README](../scripts/backup/README.md)
