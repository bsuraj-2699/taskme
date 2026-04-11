from __future__ import annotations

from urllib.parse import quote

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Prefer composing a safe DB URL from POSTGRES_* (handles special characters).
    postgres_db: str = "taskme"
    postgres_user: str = "taskme"
    postgres_password: str = "taskme_password_change_me"
    postgres_host: str = "db"
    postgres_port: int = 5432

    database_url: str = ""

    backend_cors_origin: AnyHttpUrl = "http://localhost:3000"

    jwt_secret_key: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    login_rate_limit: str = "10/minute"

    log_level: str = "INFO"
    log_dir: str = "/app/logs"

    # File upload limits
    max_file_size_mb: int = 10          # Max single file size in MB
    max_files_per_upload: int = 10      # Max files per upload request

    # Pagination defaults
    default_page_size: int = 50
    max_page_size: int = 200

    def model_post_init(self, __context) -> None:
        # Always compose from POSTGRES_* so passwords like "x@y" work without manual URL-encoding.
        pw = quote(self.postgres_password, safe="")
        self.database_url = (
            f"postgresql+psycopg://{self.postgres_user}:{pw}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
