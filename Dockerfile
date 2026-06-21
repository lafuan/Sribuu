# =============================================================================
# Sribuu — Dockerfile
# =============================================================================
# Multi-stage build: minimal image untuk production.
#
# Build:
#   docker build -t sribuu:latest .
#
# Run:
#   docker run -d --name sribuu \
#     --network host \
#     --restart always \
#     -e DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/sribuu \
#     -e SECRET_KEY="<random-secret>" \
#     sribuu:latest
#
# Catatan:
#   - Pakai --network host agar container bisa akses PostgreSQL di localhost
#   - PostgreSQL berjalan NATIVE di host (bukan container)
#   - Nginx tetap NATIVE di host sebagai reverse proxy + SSL termination
# =============================================================================

# ─── Stage 1: Install dependencies ────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy only dependency files first (better layer caching)
COPY requirements.txt pyproject.toml ./

# Install dependencies ke direktori terpisah
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ─── Stage 2: Runtime ─────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy aplikasi
COPY . .

# Non-root user untuk keamanan
RUN addgroup --system --gid 1001 sribuu && \
    adduser --system --uid 1001 --ingroup sribuu --no-create-home sribuu && \
    chown -R sribuu:sribuu /app
USER sribuu

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Jalankan dengan 2 workers (cocok VPS 2 Core)
# Gunakan --forwarded-allow-ips='*' karena di belakang Nginx reverse proxy
CMD ["uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--forwarded-allow-ips", "*"]
