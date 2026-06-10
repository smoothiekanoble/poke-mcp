"""Environment-backed settings."""

from __future__ import annotations

from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_timezone: str = Field(default="America/Chicago", alias="APP_TIMEZONE")
    mcp_host: str = Field(default="127.0.0.1", alias="MCP_HOST")
    mcp_port: int = Field(default=8000, validation_alias=AliasChoices("MCP_PORT", "PORT"))
    mcp_path: str = Field(default="/mcp", alias="MCP_PATH")
    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_service_role_key: str | None = Field(
        default=None,
        alias="SUPABASE_SERVICE_ROLE_KEY",
    )
    daniel_user_id: str | None = Field(default=None, alias="DANIEL_USER_ID")
    poke_mcp_api_key: str | None = Field(default=None, alias="POKE_MCP_API_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def supabase_configured(self) -> bool:
        return bool(
            self.supabase_url
            and self.supabase_service_role_key
            and self.daniel_user_id
        )

    @property
    def google_calendar_configured(self) -> bool:
        return False

    def timezone(self) -> ZoneInfo:
        try:
            return ZoneInfo(self.app_timezone)
        except ZoneInfoNotFoundError as exc:
            msg = f"Unknown APP_TIMEZONE: {self.app_timezone}"
            raise ValueError(msg) from exc


@lru_cache
def get_settings() -> Settings:
    return Settings()
