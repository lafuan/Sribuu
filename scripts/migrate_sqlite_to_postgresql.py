#!/usr/bin/env python3
# ruff: noqa: PLR0912, PLR0915, I001
"""
Sribuu — Data Migration: SQLite → PostgreSQL
=============================================
Migrasi seluruh data dari database SQLite ke PostgreSQL.

Cara pakai:
  1. Pastikan PostgreSQL sudah terinstall dan database sribuu sudah dibuat:
       sudo -u postgres psql -c "CREATE USER sribuu WITH PASSWORD 'sribuu_dev_2026';"
       sudo -u postgres psql -c "CREATE DATABASE sribuu OWNER sribuu;"

  2. Jalankan script ini:
       python scripts/migrate_sqlite_to_postgresql.py

  3. Script akan:
       a. Baca semua data dari SQLite
       b. Buat tabel-tabel di PostgreSQL
       c. Insert semua data ke PostgreSQL
       d. Verifikasi jumlah data

Catatan:
  - Script ini IDEMPOTEN: tabel PostgreSQL akan di-drop & recreate tiap run.
  - SQLite DB di path: /var/lib/sribuu/sribuu.db (atau via env SQLITE_DB_PATH)
  - PostgreSQL URL via env DATABASE_URL (atau default localhost)
"""

import os
import sys
from datetime import date, datetime
from typing import Any

# ─── Konfigurasi ──────────────────────────────────────────────────────────

SQLITE_DB_PATH = os.environ.get(
    "SQLITE_DB_PATH",
    "/var/lib/sribuu/sribuu.db",
)

PG_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://sribuu:sribuu_dev_2026@localhost:5432/sribuu",
)

# ─── Fungsi Bantuan ───────────────────────────────────────────────────────


def ensure_sqlite(path: str) -> bool:
    """Cek apakah SQLite DB ada."""
    return os.path.isfile(path)


def print_step(msg: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {msg}")
    print(f"{'=' * 60}")


def print_ok(msg: str) -> None:
    print(f"  ✅ {msg}")


def print_info(msg: str) -> None:
    print(f"  ℹ️  {msg}")


# ─── Migrasi Data ─────────────────────────────────────────────────────────


def migrate():
    """
    Migrasi data dari SQLite ke PostgreSQL menggunakan SQLAlchemy sync engine.
    """
    # Import di sini agar error dependency langsung ketahuan
    import sqlalchemy as sa
    from sqlalchemy import create_engine, MetaData, Table, text
    from sqlalchemy.orm import Session, sessionmaker

    # ── Connect ke SQLite ────────────────────────────────────────────
    print_step("1. Membaca database SQLite")
    sqlite_url = f"sqlite:///{SQLITE_DB_PATH}"
    sqlite_engine = create_engine(sqlite_url, echo=False)
    sqlite_meta = MetaData()
    sqlite_meta.reflect(bind=sqlite_engine)

    tables_sqlite = sorted(sqlite_meta.tables.keys())
    print_ok(f"SQLite terhubung: {SQLITE_DB_PATH}")
    print_info(f"Tabel ditemukan: {', '.join(tables_sqlite)}")

    # Baca data dari setiap tabel
    sqlite_data: dict[str, list[dict[str, Any]]] = {}
    for table_name in tables_sqlite:
        table = sqlite_meta.tables[table_name]
        with sqlite_engine.connect() as conn:
            result = conn.execute(table.select())
            rows = [dict(row._mapping) for row in result]
            sqlite_data[table_name] = rows
            print_ok(f"  {table_name}: {len(rows)} baris")

    sqlite_engine.dispose()

    # ── Connect ke PostgreSQL ────────────────────────────────────────
    print_step("2. Menyiapkan database PostgreSQL")
    pg_url = PG_DATABASE_URL.replace("+asyncpg", "+psycopg2")
    pg_engine = create_engine(pg_url, echo=False)

    # Test koneksi
    with pg_engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        pg_version = result.scalar()
    print_ok(f"PostgreSQL terhubung: {pg_version}")

    # ── Buat ulang tabel di PostgreSQL ───────────────────────────────
    print_step("3. Membuat tabel di PostgreSQL")

    # Import models untuk create_all
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    os.environ["DATABASE_URL"] = PG_DATABASE_URL

    from backend.database import Base
    import backend.models  # noqa: F401 — register all models on Base.metadata

    # Drop & create all tables
    Base.metadata.drop_all(pg_engine)
    Base.metadata.create_all(pg_engine)
    print_ok("Tabel berhasil dibuat di PostgreSQL")

    # Reflect tabel PostgreSQL
    pg_meta = MetaData()
    pg_meta.reflect(bind=pg_engine)
    tables_pg = sorted(pg_meta.tables.keys())
    print_info(f"Tabel PostgreSQL: {', '.join(tables_pg)}")

    # ── Insert data ke PostgreSQL ────────────────────────────────────
    print_step("4. Migrasi data ke PostgreSQL")

    SessionPG = sessionmaker(bind=pg_engine)
    pg_session = SessionPG()

    # Urutan insert: parent dulu baru child (FK constraint)
    insert_order = [
        "users",
        "categories",
        "payment_methods",
        "transactions",
        "transaction_templates",
        "budgets",
        "weekly_summaries",
    ]

    total_inserted = 0
    for table_name in insert_order:
        if table_name not in sqlite_data or not sqlite_data[table_name]:
            print_info(f"  {table_name}: tidak ada data (skip)")
            continue

        pg_table = pg_meta.tables.get(table_name)
        if pg_table is None:
            print_info(f"  {table_name}: tabel tidak ditemukan di PG (skip)")
            continue

        rows = sqlite_data[table_name]

        # Handle SQLite → PostgreSQL type conversions
        cleaned_rows = []
        for row in rows:
            clean = {}
            for col_name, value in row.items():
                # Konversi datetime yang masih string ke datetime object
                if isinstance(value, str) and col_name in (
                    "created_at", "updated_at", "generated_at"
                ):
                    try:
                        clean[col_name] = datetime.fromisoformat(value)
                    except ValueError:
                        clean[col_name] = value
                elif isinstance(value, str) and col_name == "transaction_date":
                    try:
                        clean[col_name] = date.fromisoformat(value)
                    except ValueError:
                        clean[col_name] = value
                else:
                    clean[col_name] = value
            cleaned_rows.append(clean)

        pg_session.execute(pg_table.insert(), cleaned_rows)
        pg_session.commit()
        total_inserted += len(cleaned_rows)
        print_ok(f"  {table_name}: {len(cleaned_rows)} baris di-insert")

    pg_session.close()

    # ── Verifikasi ───────────────────────────────────────────────────
    print_step("5. Verifikasi migrasi")
    pg_session2 = sessionmaker(bind=pg_engine)()
    all_ok = True
    for table_name in insert_order:
        pg_table = pg_meta.tables.get(table_name)
        if pg_table is None:
            continue
        count = pg_session2.query(pg_table).count()
        expected = len(sqlite_data.get(table_name, []))
        status = "✅" if count == expected else "❌"
        if count != expected:
            all_ok = False
        print(f"  {status} {table_name}: {count} baris (expected: {expected})")

    pg_session2.close()
    pg_engine.dispose()

    print_step("Hasil Migrasi")
    if all_ok:
        print_ok(f"✅ Migrasi SUKSES! {total_inserted} baris data dipindahkan.")
        print_info(f"Database: {PG_DATABASE_URL}")
        print()
        print("Langkah selanjutnya:")
        print("  1. Update service file: DATABASE_URL → PostgreSQL")
        print("  2. Restart service: sudo systemctl restart sribuu")
        print("  3. Verifikasi aplikasi berjalan: curl https://sribuu.duckdns.org/health")
    else:
        print("❌ Migrasi GAGAL — ada ketidaksesuaian data. Cek log di atas.")
        sys.exit(1)


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║  Sribuu — Data Migration: SQLite → PostgreSQL            ║
╚═══════════════════════════════════════════════════════════╝
    """)
    if not ensure_sqlite(SQLITE_DB_PATH):
        print(f"❌ SQLite database tidak ditemukan di: {SQLITE_DB_PATH}")
        print(f"   Set env SQLITE_DB_PATH jika lokasi berbeda.")
        sys.exit(1)

    migrate()
    print()
