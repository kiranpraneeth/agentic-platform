# Operations Runbook

Operational procedures and incident response guide for the Agentic Platform.

## Table of Contents

- [Emergency Contacts](#emergency-contacts)
- [Incident Response](#incident-response)
- [Common Scenarios](#common-scenarios)
- [Service Recovery](#service-recovery)
- [Database Operations](#database-operations)
- [Performance Issues](#performance-issues)
- [Security Incidents](#security-incidents)
- [Monitoring & Alerts](#monitoring--alerts)
- [Maintenance Procedures](#maintenance-procedures)

## Emergency Contacts

### On-Call Rotation

| Role | Primary | Secondary |
|------|---------|-----------|
| Platform Lead | [Name] (+1-XXX-XXX-XXXX) | [Name] (+1-XXX-XXX-XXXX) |
| DevOps Engineer | [Name] (+1-XXX-XXX-XXXX) | [Name] (+1-XXX-XXX-XXXX) |
| Backend Engineer | [Name] (+1-XXX-XXX-XXXX) | [Name] (+1-XXX-XXX-XXXX) |

### Escalation Path

1. **On-call engineer** (first responder)
2. **Team lead** (if issue not resolved in 30 minutes)
3. **Director of Engineering** (if critical impact > 1 hour)
4. **CTO** (if major outage > 2 hours)

### External Contacts

- **Cloud Provider Support:** [Support Portal Link]
- **Database Support:** [Support Portal Link]
- **CDN/DNS Provider:** [Support Portal Link]

## Incident Response

### Severity Levels

#### P0 - Critical
- **Impact:** Complete service outage
- **Response Time:** Immediate
- **Examples:**
  - API completely down
  - Database unavailable
  - Data loss or corruption
  - Security breach

#### P1 - Major
- **Impact:** Significant degradation
- **Response Time:** < 15 minutes
- **Examples:**
  - API error rate > 10%
  - Response time > 10 seconds
  - Critical feature unavailable
  - Payment processing failed

#### P2 - Minor
- **Impact:** Limited feature impact
- **Response Time:** < 1 hour
- **Examples:**
  - Non-critical feature broken
  - Performance degradation < 50%
  - Elevated error rate < 5%

#### P3 - Low
- **Impact:** Cosmetic or minimal
- **Response Time:** Next business day
- **Examples:**
  - UI glitch
  - Non-critical bug
  - Documentation error

### Incident Response Process

#### 1. Detection & Alert

```bash
# Verify the alert
curl https://api.yourdomain.com/health/ready

# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check recent logs
docker-compose -f docker-compose.prod.yml logs --tail=100 api
```

#### 2. Assess Severity

**Questions to answer:**
- Is the service accessible?
- What percentage of users are affected?
- Is data at risk?
- Are there security implications?

**Determine severity** based on impact.

#### 3. Create Incident Channel

For P0/P1 incidents:

```bash
# Slack
/incident create "API down - all requests failing"

# Update status page
# https://status.yourdomain.com
```

#### 4. Initial Response

**P0 Response (< 5 minutes):**

```bash
# Quick diagnostics
docker stats  # Check resource usage
docker-compose logs --tail=200 api | grep ERROR
curl https://api.yourdomain.com/health/ready

# If API down, restart
docker-compose -f docker-compose.prod.yml restart api

# If database issue
docker-compose -f docker-compose.prod.yml restart postgres

# Check health after restart
sleep 30
curl https://api.yourdomain.com/health/ready
```

#### 5. Investigate Root Cause

```bash
# Check application logs
docker-compose -f docker-compose.prod.yml logs --since=30m api

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs --since=30m nginx

# Check database logs
docker-compose -f docker-compose.prod.yml logs --since=30m postgres

# Check system resources
docker stats
df -h
free -h

# Check for recent deployments
git log --since="2 hours ago"

# Check Sentry for errors
# https://sentry.io/your-project
```

#### 6. Communicate Status

**Update stakeholders every 15-30 minutes:**

```markdown
**Incident Update - [TIME]**

Status: Investigating / Identified / Monitoring / Resolved
Impact: [Description]
Current Actions: [What you're doing]
ETA: [If known]
Next Update: [Time]
```

#### 7. Resolution

```bash
# Apply fix
# Document exact steps taken
```

#### 8. Verify Resolution

```bash
# Health checks
curl https://api.yourdomain.com/health/ready

# Smoke tests
# Test critical user flows

# Monitor for 30 minutes
watch -n 30 'curl -s https://api.yourdomain.com/health/ready'
```

#### 9. Post-Mortem

**Within 48 hours of P0/P1 incidents:**

Create document with:
- Timeline of events
- Root cause analysis
- Impact assessment
- Actions taken
- Lessons learned
- Action items to prevent recurrence

## Common Scenarios

### Scenario 1: API Returns 500 Errors

**Symptoms:**
- API requests failing with 500 status
- Elevated error rate in monitoring

**Investigation:**

```bash
# Check application logs
docker-compose -f docker-compose.prod.yml logs --tail=200 api | grep ERROR

# Check for exceptions in Sentry
# Look for common stack traces

# Check database connectivity
docker-compose -f docker-compose.prod.yml exec api \
    python -c "from src.db.session import engine; import asyncio; asyncio.run(engine.connect())"
```

**Common Causes & Solutions:**

1. **Database connection pool exhausted**
   ```bash
   # Check metrics
   curl http://localhost:8000/metrics | grep db_pool

   # Increase pool size in docker-compose.prod.yml
   environment:
     DATABASE_POOL_SIZE: 30  # Increase from 20

   docker-compose -f docker-compose.prod.yml restart api
   ```

2. **Memory exhaustion**
   ```bash
   # Check memory usage
   docker stats

   # Increase memory limit
   # In docker-compose.prod.yml:
   deploy:
     resources:
       limits:
         memory: 4G  # Increase from 2G

   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **External API timeout**
   ```bash
   # Check logs for timeout errors
   docker-compose logs api | grep -i timeout

   # Increase timeout in code or use circuit breaker
   ```

### Scenario 2: High Response Times

**Symptoms:**
- API latency > 2 seconds
- Users reporting slowness

**Investigation:**

```bash
# Check current response times
curl -w "@- format.txt" https://api.yourdomain.com/api/v1/agents
# format.txt: time_total: %{time_total}s

# Check slow queries in database
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U postgres -d agentic_db -c \
    "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check cache hit rate
curl http://localhost:8000/metrics | grep cache_hit

# Check system load
uptime
top
```

**Solutions:**

1. **Database query optimization**
   ```bash
   # Add missing indexes
   docker-compose run --rm api python -c "
   from src.db.session import SessionLocal
   # Analyze slow queries and add indexes
   "
   ```

2. **Increase cache TTL**
   ```python
   # In src/core/cache.py, increase TTL for hot data
   CACHE_TTL = 3600  # 1 hour instead of 300 seconds
   ```

3. **Scale horizontally**
   ```bash
   # Add more API replicas (requires load balancer)
   # Not applicable for single-server deployment
   # Consider upgrading server resources
   ```

### Scenario 3: Database is Full

**Symptoms:**
- Disk space alerts
- Database write errors

**Investigation:**

```bash
# Check disk usage
df -h
docker system df

# Check database size
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U postgres -d agentic_db -c \
    "SELECT pg_size_pretty(pg_database_size('agentic_db'));"

# Check table sizes
docker-compose exec postgres psql -U postgres -d agentic_db -c \
    "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
     FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"
```

**Solutions:**

1. **Clean old data**
   ```bash
   # Archive old logs/events
   docker-compose exec postgres psql -U postgres -d agentic_db -c \
       "DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';"

   # Vacuum database
   docker-compose exec postgres psql -U postgres -d agentic_db -c "VACUUM FULL;"
   ```

2. **Clean Docker resources**
   ```bash
   docker system prune -a --volumes
   ```

3. **Expand storage**
   ```bash
   # Resize volume (cloud provider specific)
   # Or migrate to larger disk
   ```

### Scenario 4: Memory Leak

**Symptoms:**
- Gradual memory increase
- OOM (Out of Memory) errors
- Container restarts

**Investigation:**

```bash
# Monitor memory over time
watch -n 5 docker stats api

# Check for memory leaks in Python
docker-compose exec api python -c "
import sys
import gc
gc.collect()
print(f'Objects: {len(gc.get_objects())}')
print(f'Memory: {sys.getsizeof(gc.get_objects())}')
"

# Check Sentry for memory-related errors
```

**Solutions:**

1. **Restart service**
   ```bash
   docker-compose -f docker-compose.prod.yml restart api
   ```

2. **Implement periodic restarts**
   ```bash
   # Add to crontab
   0 3 * * * cd /opt/agentic-platform && docker-compose -f docker-compose.prod.yml restart api
   ```

3. **Fix memory leak in code**
   - Review recent code changes
   - Check for unclosed connections
   - Review caching logic
   - Profile memory usage locally

### Scenario 5: SSL Certificate Expired

**Symptoms:**
- HTTPS connections failing
- Browser certificate warnings

**Investigation:**

```bash
# Check certificate expiration
openssl x509 -in nginx/ssl/cert.pem -noout -dates

# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -noout -checkend 86400
```

**Solutions:**

1. **Renew Let's Encrypt certificate**
   ```bash
   # Renew certificate
   sudo certbot renew

   # Copy new certificate
   sudo cp /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem nginx/ssl/cert.pem
   sudo cp /etc/letsencrypt/live/api.yourdomain.com/privkey.pem nginx/ssl/key.pem

   # Restart nginx
   docker-compose -f docker-compose.prod.yml restart nginx

   # Verify
   curl -v https://api.yourdomain.com 2>&1 | grep -i expire
   ```

2. **Automate renewal** (prevent future issues)
   ```bash
   # Set up auto-renewal cron
   sudo crontab -e
   # Add: 0 0 1 * * certbot renew --deploy-hook "..."
   ```

## Service Recovery

### Complete Service Recovery

If all services are down:

```bash
cd /opt/agentic-platform

# 1. Stop all services
docker-compose -f docker-compose.prod.yml down

# 2. Check Docker daemon
sudo systemctl status docker
sudo systemctl restart docker

# 3. Start services in order
docker-compose -f docker-compose.prod.yml up -d postgres redis
sleep 15

docker-compose -f docker-compose.prod.yml up -d api
sleep 10

docker-compose -f docker-compose.prod.yml up -d nginx backup

# 4. Verify each service
docker-compose -f docker-compose.prod.yml ps
curl https://api.yourdomain.com/health/ready

# 5. Monitor logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Database Recovery

If database is corrupted:

```bash
# 1. Stop API
docker-compose -f docker-compose.prod.yml stop api

# 2. Find latest backup
ls -lt backups/backup_agentic_db_*.sql.gz | head -1

# 3. Restore from backup
BACKUP_FILE=backups/backup_agentic_db_20250122_020015.sql.gz

# Verify checksum
sha256sum -c ${BACKUP_FILE}.sha256

# Drop and recreate database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE agentic_db;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE agentic_db;"

# Restore
gunzip -c ${BACKUP_FILE} | \
    docker exec -i agentic-postgres-prod psql -U postgres -d agentic_db

# 4. Run migrations
docker-compose run --rm api alembic upgrade head

# 5. Start API
docker-compose -f docker-compose.prod.yml start api

# 6. Verify
curl https://api.yourdomain.com/health/ready
```

## Database Operations

### Database Maintenance

```bash
# Vacuum database (reclaim space)
docker-compose exec postgres psql -U postgres -d agentic_db -c "VACUUM FULL ANALYZE;"

# Reindex database
docker-compose exec postgres psql -U postgres -d agentic_db -c "REINDEX DATABASE agentic_db;"

# Update statistics
docker-compose exec postgres psql -U postgres -d agentic_db -c "ANALYZE;"
```

### Query Performance Analysis

```bash
# Enable slow query logging
docker-compose exec postgres psql -U postgres -c \
    "ALTER SYSTEM SET log_min_duration_statement = 1000;"  # Log queries > 1s

# Check slow queries
docker-compose exec postgres psql -U postgres -d agentic_db -c \
    "SELECT query, calls, total_time, mean_time
     FROM pg_stat_statements
     ORDER BY mean_time DESC
     LIMIT 20;"

# Explain specific query
docker-compose exec postgres psql -U postgres -d agentic_db -c \
    "EXPLAIN ANALYZE SELECT * FROM agents WHERE tenant_id = 'xxx';"
```

### Database Backup & Restore

See [Backup README](../scripts/backup/README.md) for detailed procedures.

**Quick reference:**

```bash
# Manual backup
docker-compose exec backup /usr/local/bin/backup.sh

# List backups
ls -lh backups/

# Restore from backup
gunzip -c backups/backup_agentic_db_TIMESTAMP.sql.gz | \
    docker exec -i agentic-postgres-prod psql -U postgres -d agentic_db
```

## Performance Issues

### CPU Spikes

**Investigation:**

```bash
# Check CPU usage
top
docker stats

# Check for CPU-intensive queries
docker-compose exec postgres psql -U postgres -d agentic_db -c \
    "SELECT pid, query, state, wait_event
     FROM pg_stat_activity
     WHERE state != 'idle'
     ORDER BY query_start;"
```

**Solutions:**

1. Kill long-running queries
   ```bash
   # Find query PID
   docker-compose exec postgres psql -U postgres -d agentic_db -c \
       "SELECT pid, query FROM pg_stat_activity WHERE state = 'active';"

   # Kill query
   docker-compose exec postgres psql -U postgres -d agentic_db -c \
       "SELECT pg_terminate_backend(PID);"
   ```

2. Add rate limiting
   ```python
   # Already configured in src/core/rate_limit.py
   # Adjust limits if needed
   ```

### High Network Traffic

**Investigation:**

```bash
# Check network usage
iftop
nethogs

# Check nginx access logs
docker-compose logs nginx | tail -1000 | awk '{print $1}' | sort | uniq -c | sort -rn | head -20
```

**Solutions:**

```bash
# Identify and block abusive IPs
# In nginx/nginx.conf:
# deny 1.2.3.4;

# Restart nginx
docker-compose restart nginx

# Or use fail2ban for automatic blocking
```

## Security Incidents

### Suspected Breach

**Immediate actions:**

1. **Isolate affected systems**
   ```bash
   # Block external access temporarily
   sudo ufw deny 80/tcp
   sudo ufw deny 443/tcp
   ```

2. **Preserve evidence**
   ```bash
   # Copy all logs
   mkdir -p /tmp/incident-$(date +%Y%m%d)
   docker-compose logs > /tmp/incident-$(date +%Y%m%d)/docker-logs.txt
   cp -r nginx/logs /tmp/incident-$(date +%Y%m%d)/
   cp -r logs /tmp/incident-$(date +%Y%m%d)/
   ```

3. **Notify security team**
   - Contact security team immediately
   - Document timeline of events
   - Preserve all evidence

4. **Investigate**
   ```bash
   # Check for unauthorized access
   docker-compose logs api | grep -i "401\|403\|unauthorized"

   # Check for suspicious database queries
   docker-compose exec postgres psql -U postgres -d agentic_db -c \
       "SELECT * FROM audit_logs WHERE created_at > NOW() - INTERVAL '24 hours'
        ORDER BY created_at DESC;"

   # Check for file changes
   find / -type f -mtime -1
   ```

### Credential Compromise

If API keys or secrets are compromised:

```bash
# 1. Rotate all secrets immediately
cd /opt/agentic-platform/secrets
openssl rand -base64 64 > secret_key.txt
openssl rand -base64 64 > jwt_secret.txt

# 2. Update API keys
echo "new-anthropic-key" > anthropic_api_key.txt
echo "new-openai-key" > openai_api_key.txt

# 3. Restart services
docker-compose -f docker-compose.prod.yml restart api

# 4. Invalidate all user sessions
docker-compose exec redis redis-cli FLUSHDB

# 5. Notify affected users
```

## Monitoring & Alerts

### Key Metrics to Monitor

**Application Metrics:**
- Request rate (requests/second)
- Error rate (%)
- Response time (p50, p95, p99)
- API availability (uptime %)

**Infrastructure Metrics:**
- CPU usage (%)
- Memory usage (%)
- Disk usage (%)
- Network I/O

**Database Metrics:**
- Connection pool usage
- Query response time
- Active connections
- Replication lag (if applicable)

**Business Metrics:**
- Active users
- Agent executions
- Token usage
- Revenue per hour

### Alert Thresholds

```yaml
Critical Alerts (Page immediately):
  - API down (health check fails)
  - Error rate > 10%
  - Database down
  - Disk usage > 90%
  - Memory usage > 95%

Warning Alerts (Notify during business hours):
  - Error rate > 5%
  - Response time p95 > 5s
  - Disk usage > 80%
  - Memory usage > 85%
  - CPU usage > 80% for 10 minutes

Info Alerts (Log only):
  - Deployment completed
  - Backup completed
  - Certificate renewed
```

## Maintenance Procedures

### Planned Maintenance

**1. Schedule maintenance window**
- Low-traffic period (e.g., 2-4 AM)
- Notify users 48 hours in advance
- Update status page

**2. Preparation**
```bash
# Backup database
docker-compose exec backup /usr/local/bin/backup.sh

# Test rollback procedure
# Document exact steps
```

**3. During maintenance**
```bash
# Enable maintenance mode (if implemented)
# Or update status page

# Perform updates
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head
docker-compose -f docker-compose.prod.yml up -d

# Verify
curl https://api.yourdomain.com/health/ready
```

**4. Post-maintenance**
- Verify all services healthy
- Run smoke tests
- Monitor for 30 minutes
- Update status page
- Send completion notification

### Monthly Maintenance Checklist

- [ ] Review and rotate secrets
- [ ] Update dependencies (`poetry update`)
- [ ] Apply security patches
- [ ] Review disk usage and clean up
- [ ] Test backup restoration
- [ ] Review and update documentation
- [ ] Review access logs for anomalies
- [ ] Performance review
- [ ] Cost optimization review

## Additional Resources

- [Docker Deployment Guide](./DOCKER_DEPLOYMENT.md)
- [Observability Guide](./OBSERVABILITY.md)
- [Sentry Documentation](./SENTRY.md)
- [Performance Guide](./PERFORMANCE.md)
- [Testing Guide](./TESTING_GUIDE.md)
