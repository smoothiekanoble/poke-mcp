"""Dashboard MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from poke_mcp.services.dashboard_service import DashboardService
from poke_mcp.tools.habittracker_tools import safe_tool_call


def register_dashboard_tools(
    mcp: Any,
    dashboard_service_factory: Callable[[], DashboardService],
) -> None:
    @mcp.tool
    def get_today_dashboard() -> dict[str, Any]:
        """Return today's HabitTracker completion summary."""
        return safe_tool_call(lambda: dashboard_service_factory().get_today_dashboard())

