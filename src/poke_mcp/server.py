"""FastMCP server entrypoint."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP

from poke_mcp.clients.supabase_client import build_supabase_client
from poke_mcp.config import Settings, get_settings
from poke_mcp.services.dashboard_service import DashboardService
from poke_mcp.services.habittracker_service import HabitTrackerService
from poke_mcp.tools.blocked_tools import register_blocked_tools
from poke_mcp.tools.dashboard_tools import register_dashboard_tools
from poke_mcp.tools.habittracker_tools import register_habittracker_tools
from poke_mcp.tools.health_tools import register_health_tools


def create_mcp(
    *,
    settings: Settings | None = None,
    supabase_client: Any | None = None,
    today_provider: Callable[[], str] | None = None,
) -> FastMCP:
    resolved_settings = settings or get_settings()

    mcp = FastMCP("Poke HabitTracker MCP")

    def habittracker_service_factory() -> HabitTrackerService:
        client = supabase_client or build_supabase_client(resolved_settings)
        return HabitTrackerService(
            client,
            resolved_settings,
            today_provider=today_provider,
        )

    def dashboard_service_factory() -> DashboardService:
        return DashboardService(habittracker_service_factory())

    register_health_tools(mcp, resolved_settings)
    register_habittracker_tools(mcp, habittracker_service_factory)
    register_dashboard_tools(mcp, dashboard_service_factory)
    register_blocked_tools(mcp)
    return mcp


mcp = create_mcp()


def main() -> None:
    settings = get_settings()
    mcp.run(
        transport="http",
        host=settings.mcp_host,
        port=settings.mcp_port,
        path=settings.mcp_path,
    )


if __name__ == "__main__":
    main()
