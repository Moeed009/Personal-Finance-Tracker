from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Personal Finance Tracker"
    database_url: str
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str | None = None
    import_bucket_name: str = "csv-imports"
    max_upload_size_mb: int = 5
    default_currency: str = "PKR"
    frontend_url: str = "http://localhost:5173"
    cookie_secure: bool = False
    access_cookie_max_age: int = 3600
    refresh_cookie_max_age: int = 60 * 60 * 24 * 30
    cors_origins: list[str] = []
    account_deletion_grace_hours: int = 2
    purge_interval_minutes: int = 10

    
    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
