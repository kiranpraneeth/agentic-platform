# Dockerfile for automated PostgreSQL backup service
FROM postgres:16-alpine

# Install required tools
RUN apk add --no-cache \
    aws-cli \
    bash \
    curl \
    dcron \
    tzdata

# Set timezone (can be overridden via environment)
ENV TZ=UTC

# Create backup directory
RUN mkdir -p /backups /var/log/cron

# Copy backup script
COPY backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

# Create crontab file
RUN echo '# Automated backup cron job' > /etc/crontabs/root && \
    echo '# Default: Daily at 2 AM UTC' >> /etc/crontabs/root && \
    echo '# Override with BACKUP_SCHEDULE environment variable' >> /etc/crontabs/root && \
    echo '0 2 * * * /usr/local/bin/backup.sh >> /var/log/cron/backup-cron.log 2>&1' >> /etc/crontabs/root

# Copy entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Health check
HEALTHCHECK --interval=1h --timeout=10s --start-period=10s --retries=1 \
    CMD test -f /backups/backup.log || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
