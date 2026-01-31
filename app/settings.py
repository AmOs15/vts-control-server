from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = "localhost"
    port: int = 8001
    plugin_name: str = "vts-control-server"
    plugin_developer: str = "vts-control-server"
    token_path: str = ".secrets/vts_token.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="VTS_",
        case_sensitive=False,
    )
