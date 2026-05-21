import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_origins(value: str) -> list[str]:
    if not value or not value.strip():
        return []
    return [origin.strip() for origin in value.split(",") if origin.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    debug: bool = False
    database_url: str = "sqlite:///./analytics.db"
    api_key: str = ""
    allowed_origins: str = ""
    dashboard_username: str = "admin"
    dashboard_password: str = ""
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_claims_sub: str = "mailto:admin@localhost"
    push_max_fail_count: int = 5

    @property
    def allowed_origins_list(self) -> list[str]:
        origins = _parse_origins(self.allowed_origins)
        if self.debug:
            localhost = [
                "http://localhost:8000",
                "http://127.0.0.1:8000",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
            return list(dict.fromkeys(origins + localhost))
        return origins

    def validate_production(self) -> None:
        if self.debug:
            return
        missing = []
        if not self.api_key:
            missing.append("API_KEY")
        if not self.dashboard_password:
            missing.append("DASHBOARD_PASSWORD")
        if missing:
            raise RuntimeError(
                f"Production mode (DEBUG=false) requires: {', '.join(missing)}. "
                "Set them in .env or environment variables."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
