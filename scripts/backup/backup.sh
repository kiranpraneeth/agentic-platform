#!/bin/bash
#
# Automated PostgreSQL backup script for Agentic Platform
# Supports local storage and optional S3 upload
#

set -euo pipefail

# Configuration from environment
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-agentic_db}"
DB_USER=$(cat "${DB_USER_FILE:-/run/secrets/db_user}")
DB_PASSWORD=$(cat "${DB_PASSWORD_FILE:-/run/secrets/db_password}")
BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Timestamp for backup filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"
BACKUP_LOG="${BACKUP_DIR}/backup.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${BACKUP_LOG}"
}

# Error handler
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

log "Starting backup of database: ${DB_NAME}"
log "Backup file: ${BACKUP_FILE}"

# Perform backup
PGPASSWORD="${DB_PASSWORD}" pg_dump \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --format=plain \
    --no-owner \
    --no-acl \
    --verbose \
    2>> "${BACKUP_LOG}" \
    | gzip > "${BACKUP_FILE}" \
    || error_exit "pg_dump failed"

# Verify backup file was created
if [ ! -f "${BACKUP_FILE}" ]; then
    error_exit "Backup file was not created"
fi

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
log "Backup completed successfully. Size: ${BACKUP_SIZE}"

# Calculate checksum
CHECKSUM=$(sha256sum "${BACKUP_FILE}" | awk '{print $1}')
echo "${CHECKSUM}  ${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
log "Checksum: ${CHECKSUM}"

# Upload to S3 if configured
if [ -n "${S3_BUCKET}" ]; then
    log "Uploading backup to S3: s3://${S3_BUCKET}/"

    aws s3 cp "${BACKUP_FILE}" \
        "s3://${S3_BUCKET}/backups/$(basename ${BACKUP_FILE})" \
        --region "${AWS_REGION}" \
        --storage-class STANDARD_IA \
        || log "WARNING: S3 upload failed"

    aws s3 cp "${BACKUP_FILE}.sha256" \
        "s3://${S3_BUCKET}/backups/$(basename ${BACKUP_FILE}.sha256)" \
        --region "${AWS_REGION}" \
        || log "WARNING: S3 checksum upload failed"

    log "S3 upload completed"
fi

# Remove old backups (local)
log "Cleaning up old backups (retention: ${BACKUP_RETENTION_DAYS} days)"
find "${BACKUP_DIR}" -name "backup_${DB_NAME}_*.sql.gz" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "backup_${DB_NAME}_*.sql.gz.sha256" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete

# List remaining backups
BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "backup_${DB_NAME}_*.sql.gz" -type f | wc -l)
log "Local backups remaining: ${BACKUP_COUNT}"

# Remove old backups from S3 if configured
if [ -n "${S3_BUCKET}" ]; then
    log "Cleaning up old S3 backups"

    # Get list of old backups
    OLD_BACKUPS=$(aws s3 ls "s3://${S3_BUCKET}/backups/" --region "${AWS_REGION}" \
        | awk '{print $4}' \
        | grep "backup_${DB_NAME}_" \
        | sort -r \
        | tail -n +$((BACKUP_RETENTION_DAYS + 1)))

    # Delete old backups
    for backup in ${OLD_BACKUPS}; do
        aws s3 rm "s3://${S3_BUCKET}/backups/${backup}" --region "${AWS_REGION}" || true
        log "Deleted old S3 backup: ${backup}"
    done
fi

log "Backup process completed"

# Exit successfully
exit 0
