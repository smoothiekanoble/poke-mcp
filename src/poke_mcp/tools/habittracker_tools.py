"""HabitTracker MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from poke_mcp.services.habittracker_service import (
    HabitTrackerService,
    MissingConfigurationError,
)


def safe_tool_call(operation: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return operation()
    except MissingConfigurationError as exc:
        return {
            "status": "not_configured",
            "message": str(exc),
        }


def register_habittracker_tools(
    mcp: Any,
    habittracker_service_factory: Callable[[], HabitTrackerService],
) -> None:
    @mcp.tool
    def list_today_habits() -> dict[str, Any]:
        """List today's active HabitTracker habits and completion status."""
        return safe_tool_call(lambda: habittracker_service_factory().list_today_habits())

    @mcp.tool
    def complete_habit(habit_name: str) -> dict[str, Any]:
        """Mark today's matching HabitTracker habit complete."""
        return safe_tool_call(lambda: habittracker_service_factory().complete_habit(habit_name))

    @mcp.tool
    def uncomplete_habit(habit_name: str) -> dict[str, Any]:
        """Mark today's matching HabitTracker habit incomplete without deleting logs."""
        return safe_tool_call(lambda: habittracker_service_factory().uncomplete_habit(habit_name))

