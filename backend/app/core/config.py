import json
from typing import Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object loaded from .env or environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Server
    APP_TITLE: str = "Quantum DNA Sequence Analyzer"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # CORS – can be string "*" or comma-separated origins or list of strings
    CORS_ORIGINS: Union[str, list[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @property
    def cors_origin_list(self) -> list[str]:
        v = self.CORS_ORIGINS
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                return []
            if stripped == "*":
                return ["*"]
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    return json.loads(stripped)
                except Exception:
                    pass
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return []


settings = Settings()
