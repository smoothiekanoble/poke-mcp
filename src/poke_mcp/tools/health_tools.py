"""Health MCP tool."""

from __future__ import annotations

from typing import Any

from poke_mcp.auth import api_key_configured
from poke_mcp.config import Settings


def build_health_payload(settings: Settings) -> dict[str, Any]:
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "timezone": settings.app_timezone,
        "supabase_configured": settings.supabase_configured,
        "google_calendar_configured": settings.google_calendar_configured,
        "api_key_configured": api_key_configured(settings),
        "enabled_tool_groups": ["health", "habittracker", "dashboard", "metrics"],
        "blocked_tool_groups": ["tasks", "checkins", "calendar"],
    }


def register_health_tools(mcp: Any, settings: Settings) -> None:
    @mcp.tool
    def health() -> dict[str, Any]:
        """Return secret-safe server health and configuration status."""
        return build_health_payload(settings)

