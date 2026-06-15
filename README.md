# Sribuu — Aplikasi Pencatatan Pengeluaran Harian

Aplikasi web ringan untuk mencatat pengeluaran harian. Dibangun dengan Python FastAPI + SQLite + Jinja2 + HTMX.

## Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Backend | Python 3.11+ / FastAPI |
| Database | SQLite + SQLAlchemy 2.0 |
| Frontend | Jinja2 + HTMX + Alpine.js + Tailwind CSS CDN |
| Chart | Chart.js CDN |
| Server | Uvicorn + Nginx |

## Menjalankan (Development)

```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Jalankan
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Buka http://localhost:8000

## Struktur Proyek

```
Sribuu/
├── backend/
│   ├── main.py          # Entry point FastAPI
│   ├── config.py        # Konfigurasi aplikasi
│   ├── database.py      # Database connection + session
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── routers/         # API routes
│   ├── services/        # Business logic
│   └── utils/           # Helpers (security, formatting)
├── frontend/
│   └── templates/       # Jinja2 templates
├── docs/                # Dokumentasi
└── requirements.txt
```

## Lisensi

MIT
