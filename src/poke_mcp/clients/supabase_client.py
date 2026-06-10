"""Supabase client construction."""

from __future__ import annotations

from typing import Any

from supabase import create_client

from poke_mcp.config import Settings


def build_supabase_client(settings: Settings) -> Any:
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL is required")
    if not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

