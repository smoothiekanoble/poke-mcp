"""FastMCP server entrypoint."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from poke_mcp.auth import PokeApiKeyVerifier, api_key_configured
from poke_mcp.clients.supabase_client import build_supabase_client
from poke_mcp.config import Settings, get_settings
from poke_mcp.services.dashboard_service import DashboardService
from poke_mcp.services.habittracker_service import HabitTrackerService
from poke_mcp.services.metrics_service import MetricsService
from poke_mcp.tools.dashboard_tools import register_dashboard_tools
from poke_mcp.tools.habittracker_tools import register_habittracker_tools
from poke_mcp.tools.health_tools import build_health_payload, register_health_tools
from poke_mcp.tools.metrics_tools import register_metrics_tools

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


def create_mcp(
    *,
    settings: Settings | None = None,
    supabase_client: Any | None = None,
    today_provider: Callable[[], str] | None = None,
) -> FastMCP:
    resolved_settings = settings or get_settings()
    auth_required = api_key_configured(resolved_settings)
    auth = (
        PokeApiKeyVerifier(resolved_settings.poke_mcp_api_key)
        if resolved_settings.poke_mcp_api_key
        else None
    )

    logger.info(
        "Creating Poke MCP server auth_required=%s supabase_configured=%s mcp_path=%s",
        auth_required,
        resolved_settings.supabase_configured,
        resolved_settings.mcp_path,
    )

    mcp = FastMCP("Poke HabitTracker MCP", auth=auth)

    def habittracker_service_factory() -> HabitTrackerService:
        client = supabase_client or build_supabase_client(resolved_settings)
        return HabitTrackerService(
            client,
            resolved_settings,
            today_provider=today_provider,
        )

    def dashboard_service_factory() -> DashboardService:
        return DashboardService(habittracker_service_factory())

    def metrics_service_factory() -> MetricsService:
        client = supabase_client or build_supabase_client(resolved_settings)
        return MetricsService(
            client,
            resolved_settings,
            today_provider=today_provider,
        )

    register_health_tools(mcp, resolved_settings)
    register_habittracker_tools(mcp, habittracker_service_factory)
    register_dashboard_tools(mcp, dashboard_service_factory)
    register_metrics_tools(mcp, metrics_service_factory)

    @mcp.custom_route("/health", methods=["GET"])
    async def http_health(request: Request) -> JSONResponse:
        """HTTP health check for deployment platforms."""
        _ = request
        return JSONResponse(build_health_payload(resolved_settings))

    return mcp


configure_logging()
mcp = create_mcp()


def main() -> None:
    settings = get_settings()
    logger.info(
        "Starting Poke MCP server host=%s port=%s path=%s auth_required=%s",
        settings.mcp_host,
        settings.mcp_port,
        settings.mcp_path,
        api_key_configured(settings),
    )
    mcp.run(
        transport="http",
        host=settings.mcp_host,
        port=settings.mcp_port,
        path=settings.mcp_path,
    )


if __name__ == "__main__":
    main()
