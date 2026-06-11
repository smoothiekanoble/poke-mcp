"""Read-only HabitTracker metric MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from poke_mcp.services.metrics_service import MetricsService
from poke_mcp.tools.habittracker_tools import safe_tool_call

# Poke's MCP config already enables habittracker; tag weight tools there so they
# are not gated behind a separate metrics group toggle in Poke.
_HABITTRACKER_GROUP = {"habittracker"}


def register_metrics_tools(
    mcp: Any,
    metrics_service_factory: Callable[[], MetricsService],
) -> None:
    @mcp.tool(tags=_HABITTRACKER_GROUP, meta={"tool_group": "habittracker"})
    def get_latest_body_weight() -> dict[str, Any]:
        """Return the most recent HabitTracker daily body-weight metric."""
        return safe_tool_call(lambda: metrics_service_factory().get_latest_body_weight())

    @mcp.tool(tags=_HABITTRACKER_GROUP, meta={"tool_group": "habittracker"})
    def get_body_weight_history(days: int = 90) -> dict[str, Any]:
        """Return HabitTracker daily body-weight metrics for the last N days."""
        return safe_tool_call(lambda: metrics_service_factory().get_body_weight_history(days))

    @mcp.tool(tags=_HABITTRACKER_GROUP, meta={"tool_group": "habittracker"})
    def get_body_weight_trend(days: int = 30) -> dict[str, Any]:
        """Return HabitTracker body-weight trend stats over N days."""
        return safe_tool_call(lambda: metrics_service_factory().get_body_weight_trend(days))

    @mcp.tool(tags=_HABITTRACKER_GROUP, meta={"tool_group": "habittracker"})
    def get_metric_summary(metric_type: str, days: int = 30) -> dict[str, Any]:
        """Return HabitTracker summary stats for a daily metric type over N days."""
        return safe_tool_call(
            lambda: metrics_service_factory().get_metric_summary(metric_type, days)
        )
