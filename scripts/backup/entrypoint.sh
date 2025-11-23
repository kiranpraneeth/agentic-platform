#!/bin/bash
#
# Entrypoint script for backup service
# Sets up cron schedule and starts backup daemon
#

set -euo pipefail

# Default backup schedule: Daily at 2 AM UTC
BACKUP_SCHEDULE="${BACKUP_SCHEDULE:-0 2 * * *}"

echo "=== Agentic Platform Backup Service ==="
echo "Backup schedule: ${BACKUP_SCHEDULE}"
echo "Backup retention: ${BACKUP_RETENTION_DAYS:-30} days"
echo "Database: ${DB_NAME:-agentic_db}@${DB_HOST:-postgres}:${DB_PORT:-5432}"

if [ -n "${S3_BUCKET:-}" ]; then
    echo "S3 backup enabled: s3://${S3_BUCKET}/backups/"
else
    echo "S3 backup disabled (no S3_BUCKET configured)"
fi

# Update crontab with configured schedule
echo "# Automated backup cron job" > /etc/crontabs/root
echo "${BACKUP_SCHEDULE} /usr/local/bin/backup.sh >> /var/log/cron/backup-cron.log 2>&1" >> /etc/crontabs/root

# Run initial backup on startup
echo ""
echo "Running initial backup on startup..."
/usr/local/bin/backup.sh

# Start cron daemon in foreground
echo ""
echo "Starting cron daemon..."
echo "Backup service is now running"
echo "========================================"

# Run crond in foreground
exec crond -f -l 2
