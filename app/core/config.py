from datetime import timedelta

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Garante o driver psycopg v3, mesmo se a URI vier como postgresql:// do Supabase/Render."""
    value = url.strip()
    if not value:
        return value

    replacements = (
        ("postgresql+psycopg2://", "postgresql+psycopg://"),
        ("postgres://", "postgresql+psycopg://"),
        ("postgresql://", "postgresql+psycopg://"),
    )
    for old, new in replacements:
        if value.startswith(old):
            return new + value[len(old) :]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "RotaHub"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = ""
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False

    jwt_secret_key: str = "change-me-in-production-rotahub-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    admin_name: str = "Administrador"
    admin_email: str = "admin@rotahub.app"
    admin_password: str = "Admin@123"

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_database_url(value)
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        origins: list[str] = []
        for raw in self.cors_origins.split(","):
            origin = raw.strip().strip("\"'")
            if not origin:
                continue
            origins.append(origin.rstrip("/"))
        return origins

    @property
    def has_database(self) -> bool:
        return bool(self.database_url.strip())

    @property
    def uses_transaction_pooler(self) -> bool:
        """Supabase expõe o pooler (PgBouncer em modo transaction) na porta 6543."""
        return "pooler." in self.database_url and ":6543" in self.database_url

    @property
    def access_token_expires(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)

    @property
    def refresh_token_expires(self) -> timedelta:
        return timedelta(days=self.refresh_token_expire_days)


settings = Settings()
