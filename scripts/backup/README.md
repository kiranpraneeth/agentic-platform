# Database Backup System

Automated PostgreSQL backup service for the Agentic Platform with local and S3 storage support.

## Features

- **Automated backups** via cron schedule (default: daily at 2 AM UTC)
- **Compression** using gzip to minimize storage
- **Integrity verification** with SHA256 checksums
- **S3 upload** support for off-site backups (optional)
- **Retention policy** for automatic cleanup of old backups (default: 30 days)
- **Logging** with detailed backup reports
- **Initial backup** on service startup

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_SCHEDULE` | `0 2 * * *` | Cron schedule (daily at 2 AM) |
| `BACKUP_RETENTION_DAYS` | `30` | Days to keep backups |
| `DB_HOST` | `postgres` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `agentic_db` | Database name |
| `DB_USER_FILE` | `/run/secrets/db_user` | Docker secret file |
| `DB_PASSWORD_FILE` | `/run/secrets/db_password` | Docker secret file |
| `BACKUP_DIR` | `/backups` | Local backup directory |
| `S3_BUCKET` | (empty) | S3 bucket for backups (optional) |
| `AWS_REGION` | `us-east-1` | AWS region for S3 |

### Cron Schedule Format

The `BACKUP_SCHEDULE` uses standard cron syntax:

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

**Examples:**
- `0 2 * * *` - Daily at 2 AM
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 0` - Weekly on Sunday at midnight
- `0 3 */7 * *` - Every 7 days at 3 AM

## Usage

### With Docker Compose (Production)

The backup service is automatically configured in `docker-compose.prod.yml`:

```bash
# Start all services including backup
docker-compose -f docker-compose.prod.yml up -d

# View backup logs
docker-compose -f docker-compose.prod.yml logs -f backup

# Check backup status
docker exec agentic-backup-prod ls -lh /backups/

# Run manual backup
docker exec agentic-backup-prod /usr/local/bin/backup.sh
```

### With S3 Storage

To enable S3 backups, configure AWS credentials and set `S3_BUCKET`:

1. **Create S3 bucket:**
   ```bash
   aws s3 mb s3://agentic-platform-backups --region us-east-1
   ```

2. **Set environment variables:**
   ```bash
   export BACKUP_S3_BUCKET=agentic-platform-backups
   export AWS_REGION=us-east-1
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   ```

3. **Start services:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Manual Backup

Run a one-time backup without starting the cron service:

```bash
docker run --rm \
  --network agentic-network \
  -v $(pwd)/backups:/backups \
  -v $(pwd)/secrets:/run/secrets \
  -e DB_HOST=postgres \
  -e DB_NAME=agentic_db \
  -e BACKUP_RETENTION_DAYS=30 \
  agentic-backup-prod \
  /usr/local/bin/backup.sh
```

## Backup File Format

Backups are stored with the following naming convention:

```
backup_<database>_<timestamp>.sql.gz
backup_<database>_<timestamp>.sql.gz.sha256
```

**Example:**
```
backup_agentic_db_20250122_020015.sql.gz
backup_agentic_db_20250122_020015.sql.gz.sha256
```

The `.sha256` file contains the checksum for integrity verification.

## Restore from Backup

### Local Restore

1. **Find the backup file:**
   ```bash
   ls -lh backups/backup_agentic_db_*.sql.gz
   ```

2. **Verify checksum:**
   ```bash
   cd backups
   sha256sum -c backup_agentic_db_20250122_020015.sql.gz.sha256
   ```

3. **Stop the API service:**
   ```bash
   docker-compose -f docker-compose.prod.yml stop api
   ```

4. **Restore the database:**
   ```bash
   # Extract and restore
   gunzip -c backups/backup_agentic_db_20250122_020015.sql.gz | \
   docker exec -i agentic-postgres-prod psql -U postgres -d agentic_db
   ```

5. **Restart services:**
   ```bash
   docker-compose -f docker-compose.prod.yml start api
   ```

### S3 Restore

1. **List available backups:**
   ```bash
   aws s3 ls s3://agentic-platform-backups/backups/
   ```

2. **Download backup:**
   ```bash
   aws s3 cp s3://agentic-platform-backups/backups/backup_agentic_db_20250122_020015.sql.gz ./
   aws s3 cp s3://agentic-platform-backups/backups/backup_agentic_db_20250122_020015.sql.gz.sha256 ./
   ```

3. **Verify and restore** (same as local restore above)

### Point-in-Time Restore

To restore to a specific point in time:

1. **Identify the backup closest to the desired time:**
   ```bash
   # List backups with timestamps
   ls -lt backups/backup_*.sql.gz
   ```

2. **Follow the restore procedure** with that backup file

## Monitoring

### Check Backup Logs

```bash
# View backup service logs
docker-compose -f docker-compose.prod.yml logs -f backup

# View cron logs
docker exec agentic-backup-prod cat /var/log/cron/backup-cron.log

# View backup script logs
docker exec agentic-backup-prod cat /backups/backup.log
```

### List Backups

```bash
# Local backups
docker exec agentic-backup-prod ls -lh /backups/

# S3 backups
aws s3 ls s3://agentic-platform-backups/backups/
```

### Verify Backup Integrity

```bash
# Check latest backup
docker exec agentic-backup-prod sh -c \
  'cd /backups && sha256sum -c $(ls -t backup_*.sha256 | head -1)'
```

## Backup Retention

The backup service automatically removes old backups based on `BACKUP_RETENTION_DAYS`:

- **Local backups:** Deleted after retention period
- **S3 backups:** Deleted after retention period (if S3 is configured)

Retention cleanup runs after each backup completes.

## Troubleshooting

### Backup Fails to Connect to Database

**Problem:** Cannot connect to PostgreSQL

**Solution:**
1. Check database is running: `docker-compose ps postgres`
2. Verify network connectivity: `docker exec backup ping postgres`
3. Check credentials in secrets files

### S3 Upload Fails

**Problem:** AWS credentials or permissions issue

**Solution:**
1. Verify AWS credentials are set correctly
2. Check S3 bucket exists and is accessible
3. Verify IAM permissions for s3:PutObject and s3:DeleteObject
4. Check network connectivity to AWS

### Backups Not Running on Schedule

**Problem:** Cron not executing backups

**Solution:**
1. Check cron logs: `docker exec backup cat /var/log/cron/backup-cron.log`
2. Verify schedule: `docker exec backup cat /etc/crontabs/root`
3. Restart backup service: `docker-compose restart backup`

### Out of Disk Space

**Problem:** `/backups` directory full

**Solution:**
1. Reduce `BACKUP_RETENTION_DAYS`
2. Enable S3 storage and reduce local retention
3. Increase disk space on host
4. Manually remove old backups:
   ```bash
   find backups/ -name "backup_*.sql.gz" -mtime +7 -delete
   ```

## Security Considerations

1. **Credentials:** Database credentials are read from Docker secrets (never in environment variables)
2. **S3 Security:** Use IAM roles with least-privilege permissions
3. **Backup Encryption:** Consider encrypting backups at rest (S3 server-side encryption)
4. **Access Control:** Restrict access to `/backups` directory
5. **Network Security:** Backup service runs on internal Docker network only

## Best Practices

1. **Test Restores Regularly:** Verify backups can be restored successfully
2. **Monitor Backup Size:** Track backup size growth over time
3. **Off-Site Storage:** Always enable S3 backups for disaster recovery
4. **Retention Policy:** Balance retention needs with storage costs
5. **Alert on Failures:** Set up monitoring alerts for backup failures
6. **Document Procedures:** Keep restore procedures updated and accessible

## Example Backup Schedule Configurations

### High-Frequency (Production Critical)

```bash
BACKUP_SCHEDULE="0 */4 * * *"  # Every 4 hours
BACKUP_RETENTION_DAYS=7        # Keep 1 week
S3_BUCKET=production-backups
```

### Standard (Production)

```bash
BACKUP_SCHEDULE="0 2 * * *"    # Daily at 2 AM
BACKUP_RETENTION_DAYS=30       # Keep 30 days
S3_BUCKET=production-backups
```

### Low-Frequency (Development)

```bash
BACKUP_SCHEDULE="0 0 * * 0"    # Weekly on Sunday
BACKUP_RETENTION_DAYS=14       # Keep 2 weeks
S3_BUCKET=""                   # No S3 (local only)
```

## Support

For issues or questions:
- Check logs: `docker-compose logs backup`
- Review documentation: `/docs/DEPLOYMENT.md`
- GitHub Issues: Report problems with backup service
