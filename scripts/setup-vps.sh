#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Sribuu — VPS Setup Script
# Run as root on a fresh Ubuntu 22.04+ VPS.
# Usage: sudo bash scripts/setup-vps.sh
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Configuration ───────────────────────────────────────────────────
APP_USER="sribuu"
APP_DIR="/opt/sribuu"
DOMAIN="${DOMAIN:-sribuu.example.com}"   # Ganti dengan domain anda
REPO_URL="https://github.com/lafuan/Sribuu.git"
BRANCH="main"
PYTHON="python3"
VENV="$APP_DIR/venv"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        Sribuu — VPS Setup Script                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── System Update ──────────────────────────────────────────────────
echo "📦 Updating system packages..."
apt-get update -y
apt-get upgrade -y

# ── Install Dependencies ────────────────────────────────────────────
echo "📦 Installing system dependencies..."
apt-get install -y \
    nginx \
    certbot python3-certbot-nginx \
    python3-venv python3-pip \
    ufw \
    fail2ban \
    git \
    curl \
    sqlite3

# ── Create App User ─────────────────────────────────────────────────
if ! id -u "$APP_USER" &>/dev/null; then
    echo "👤 Creating user: $APP_USER"
    useradd -r -s /bin/false -d "$APP_DIR" "$APP_USER"
fi

# ── Clone Repository ────────────────────────────────────────────────
if [ -d "$APP_DIR/.git" ]; then
    echo "📂 Repository already exists, pulling latest..."
    cd "$APP_DIR"
    git fetch origin "$BRANCH"
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    echo "📂 Cloning repository..."
    git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi

# ── Setup Virtual Environment ───────────────────────────────────────
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "$VENV" ]; then
    $PYTHON -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

# ── Database Directory ──────────────────────────────────────────────
mkdir -p /var/lib/sribuu
chown -R "$APP_USER:$APP_USER" /var/lib/sribuu

# ── Copy Systemd Service ────────────────────────────────────────────
echo "⚙️  Installing systemd service..."
cp "$APP_DIR/scripts/sribuu.service" /etc/systemd/system/sribuu.service
systemctl daemon-reload

# ── Copy Nginx Config ───────────────────────────────────────────────
echo "🌐 Configuring Nginx..."
cp "$APP_DIR/scripts/sribuu.nginx.conf" /etc/nginx/sites-available/sribuu
ln -sf /etc/nginx/sites-available/sribuu /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

# ── Setup Firewall (UFW) ────────────────────────────────────────────
echo "🔥 Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp       # SSH
ufw allow 80/tcp       # HTTP
ufw allow 443/tcp      # HTTPS
ufw --force enable
ufw status verbose

# ── Setup Fail2ban ──────────────────────────────────────────────────
echo "🛡️  Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
ignoreip = 127.0.0.1/8

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
backend = systemd

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
EOF

systemctl enable fail2ban
systemctl restart fail2ban

# ── Setup Logrotate ─────────────────────────────────────────────────
echo "📋 Configuring log rotation..."
cp "$APP_DIR/scripts/logrotate-sribuu.conf" /etc/logrotate.d/sribuu

# ── Setup Cron (Health Check + Backup) ──────────────────────────────
echo "⏰ Setting up cron jobs..."
# Health check every 5 minutes
cat > /etc/cron.d/sribuu-healthcheck << 'EOF'
*/5 * * * * root /opt/sribuu/scripts/healthcheck.sh >> /var/log/sribuu/healthcheck.log 2>&1
EOF

# Daily backup at 2 AM
cat > /etc/cron.d/sribuu-backup << 'EOF'
0 2 * * * root /opt/sribuu/scripts/backup.sh >> /var/log/sribuu/backup.log 2>&1
EOF

mkdir -p /var/log/sribuu

# ── Make Scripts Executable ─────────────────────────────────────────
chmod +x "$APP_DIR/scripts/"*.sh

# ── Fix Ownership ───────────────────────────────────────────────────
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# ── Enable & Start Services ─────────────────────────────────────────
echo "🚀 Starting services..."
systemctl enable sribuu
systemctl restart sribuu
systemctl enable nginx
systemctl restart nginx

# ── Certbot (Placeholder — run after DNS points to VPS) ─────────────
echo ""
echo "📜 SSL Certificate:"
echo "   Setelah DNS domain '$DOMAIN' mengarah ke VPS ini, jalankan:"
echo "   sudo certbot --nginx -d $DOMAIN"
echo ""

# ── Done ────────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Setup selesai! Akses: http://$(curl -s ifconfig.me)    ║"
echo "║  Health check: curl http://localhost:8000/health           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
