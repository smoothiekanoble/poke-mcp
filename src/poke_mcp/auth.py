"""Small auth helpers for future hosted Poke integration."""

from __future__ import annotations

import hmac

from poke_mcp.config import Settings


def api_key_configured(settings: Settings) -> bool:
    return bool(settings.poke_mcp_api_key)


def verify_api_key(provided_api_key: str | None, settings: Settings) -> bool:
    """Return true when auth is disabled or the provided API key matches."""
    if not settings.poke_mcp_api_key:
        return True
    if not provided_api_key:
        return False
    return hmac.compare_digest(provided_api_key, settings.poke_mcp_api_key)

