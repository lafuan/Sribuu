"""
Konfigurasi aplikasi Sribuu.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Aplikasi
    APP_NAME: str = "Sribuu"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    # Untuk development/testing tetap bisa pakai SQLite via env var:
    #   DATABASE_URL=sqlite+aiosqlite:///test.db
    DATABASE_URL: str = "postgresql+asyncpg://sribuu:sribuu_dev_2026@localhost:5432/sribuu"

    # Keamanan
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 hari

    # Zona waktu
    TIMEZONE: str = "Asia/Jakarta"

    # Pagination
    PAGE_SIZE: int = 25

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
