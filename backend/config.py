"""
Konfigurasi aplikasi Sribuu.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Sribuu"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database URL
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    # For local dev, you can set this in .env file.
    # Example for local SQLite: DATABASE_URL=sqlite+aiosqlite:///test.db
    DATABASE_URL: str

    # Security settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days

    # Timezone
    TIMEZONE: str = "Asia/Jakarta"

    # Pagination
    PAGE_SIZE: int = 25

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # The following makes sure that the app fails to start if
        # DATABASE_URL and SECRET_KEY are not provided.
        # In production, these should be set as environment variables.
        # For local development, they are loaded from the .env file.
        fields = {
            "DATABASE_URL": {"env": "DATABASE_URL"},
            "SECRET_KEY": {"env": "SECRET_KEY"},
        }


settings = Settings()
