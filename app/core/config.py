from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def has_database(self) -> bool:
        return bool(self.database_url.strip())

    @property
    def uses_transaction_pooler(self) -> bool:
        """Supabase expõe o pooler (PgBouncer em modo transaction) na porta 6543."""
        return "pooler." in self.database_url and ":6543" in self.database_url


settings = Settings()
