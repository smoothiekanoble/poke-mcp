"""Read-only HabitTracker metric MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from poke_mcp.services.metrics_service import MetricsService
from poke_mcp.tools.habittracker_tools import safe_tool_call


def register_metrics_tools(
    mcp: Any,
    metrics_service_factory: Callable[[], MetricsService],
) -> None:
    @mcp.tool
    def get_latest_body_weight() -> dict[str, Any]:
        """Return the most recent daily body-weight metric, with latest raw event details."""
        return safe_tool_call(lambda: metrics_service_factory().get_latest_body_weight())

    @mcp.tool
    def get_body_weight_history(days: int = 90) -> dict[str, Any]:
        """Return daily body-weight metrics for the last N days."""
        return safe_tool_call(lambda: metrics_service_factory().get_body_weight_history(days))

    @mcp.tool
    def get_body_weight_trend(days: int = 30) -> dict[str, Any]:
        """Return body-weight trend stats (first/latest/min/max/average/change) over N days."""
        return safe_tool_call(lambda: metrics_service_factory().get_body_weight_trend(days))

    @mcp.tool
    def get_metric_summary(metric_type: str, days: int = 30) -> dict[str, Any]:
        """Return summary stats for any daily metric type (e.g. body_weight) over N days."""
        return safe_tool_call(
            lambda: metrics_service_factory().get_metric_summary(metric_type, days)
        )
