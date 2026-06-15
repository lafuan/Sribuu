#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Sribuu — Rollback Script
# Rollback ke commit sebelumnya + restart service
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

APP_DIR="/opt/sribuu"
APP_SERVICE="sribuu"
BACKUP_DIR="/opt/sribuu-backups"

cd "$APP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 Initiating rollback..."

# Get current commit (for logging)
CURRENT_COMMIT=$(git rev-parse --short HEAD)
echo "Current commit: $CURRENT_COMMIT"

# Check if we can rollback
PREV_COMMIT=$(git rev-parse HEAD~1 2>/dev/null || echo "")
if [ -z "$PREV_COMMIT" ]; then
    echo "❌ No previous commit to rollback to!"
    exit 1
fi

echo "Rolling back from $CURRENT_COMMIT to $PREV_COMMIT"

# Backup current database before rollback
if [ -f /var/lib/sribuu/sribuu.db ]; then
    mkdir -p "$BACKUP_DIR"
    cp /var/lib/sribuu/sribuu.db "$BACKUP_DIR/sribuu_before_rollback_$(date +%Y%m%d_%H%M%S).db"
    echo "📦 Database backed up before rollback"
fi

# Perform rollback
git checkout "$PREV_COMMIT"

# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt

# Rollback database migration
cd backend
PYTHONPATH="$APP_DIR" alembic -c alembic.ini downgrade -1 2>/dev/null || echo "⚠️  Migration downgrade skipped (may already be at correct version)"
cd ..

# Restart service
echo "🔄 Restarting $APP_SERVICE..."
systemctl restart "$APP_SERVICE"

# Health check
sleep 3
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8000/health 2>/dev/null || echo "000")

if [ "$STATUS" = "200" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Rollback successful! Service is healthy at commit $PREV_COMMIT"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Rollback completed but health check returned $STATUS"
fi
