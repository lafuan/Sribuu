#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Sribuu — Database Backup Script
# Backup SQLite database, keep 7 days of history
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

DB_PATH="${DB_PATH:-/var/lib/sribuu/sribuu.db}"
BACKUP_DIR="${BACKUP_DIR:-/opt/sribuu-backups}"
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/sribuu_$TIMESTAMP.db.gz"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backup..."

if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found at $DB_PATH"
    exit 1
fi

# Copy + compress
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/sribuu_$TIMESTAMP.db'"
gzip "$BACKUP_DIR/sribuu_$TIMESTAMP.db"

if [ -f "$BACKUP_FILE" ]; then
    echo "✅ Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
else
    echo "❌ Backup failed"
    exit 1
fi

# Cleanup old backups
DELETED=$(find "$BACKUP_DIR" -name "sribuu_*.db.gz" -type f -mtime "+$RETENTION_DAYS" -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "🧹 Cleaned up $DELETED old backup(s)"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup complete. Total backups: $(find "$BACKUP_DIR" -name "sribuu_*.db.gz" | wc -l)"
