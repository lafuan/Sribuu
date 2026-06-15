#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Sribuu — Health Check Script
# Cek endpoint /health, restart service jika gagal
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
SERVICE="sribuu"
MAX_RETRIES=3
RETRY_DELAY=2

for i in $(seq 1 $MAX_RETRIES); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$HEALTH_URL" 2>/dev/null || echo "000")

    if [ "$STATUS" = "200" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Health check OK (attempt $i) — status: $STATUS"
        exit 0
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Health check attempt $i/$MAX_RETRIES — status: $STATUS"
    sleep "$RETRY_DELAY"
done

# All attempts failed — restart service
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Health check FAILED after $MAX_RETRIES attempts!"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 Restarting $SERVICE..."

systemctl restart "$SERVICE"
sleep 5

# Verify after restart
FINAL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$HEALTH_URL" 2>/dev/null || echo "000")
if [ "$FINAL_STATUS" = "200" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Service recovered after restart — status: $FINAL_STATUS"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🆘 CRITICAL: Service still down after restart — status: $FINAL_STATUS"
    exit 1
fi
