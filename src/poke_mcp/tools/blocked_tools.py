"""Graceful blocked responses for future schema-dependent tools."""

from __future__ import annotations

from typing import Any


def blocked_task_response() -> dict[str, Any]:
    return {
        "status": "blocked",
        "missing_schema": "tasks",
        "message": (
            "HabitTracker schema is missing tasks. Add a HabitTracker tasks migration "
            "before enabling this tool."
        ),
    }


def blocked_checkin_response() -> dict[str, Any]:
    return {
        "status": "blocked",
        "missing_schema": "daily_checkins",
        "message": (
            "HabitTracker schema is missing daily check-ins or health logs. Add an "
            "explicit HabitTracker schema before enabling this tool."
        ),
    }


def register_blocked_tools(mcp: Any) -> None:
    @mcp.tool
    def list_today_tasks() -> dict[str, Any]:
        """Blocked until HabitTracker has a tasks schema."""
        return blocked_task_response()

    @mcp.tool
    def create_task(
        title: str,
        due_date: str | None = None,
        notes: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Blocked until HabitTracker has a tasks schema."""
        _ = (title, due_date, notes, category)
        return blocked_task_response()

    @mcp.tool
    def complete_task(task_name: str) -> dict[str, Any]:
        """Blocked until HabitTracker has a tasks schema."""
        _ = task_name
        return blocked_task_response()

    @mcp.tool
    def log_daily_checkin(
        weight: float | None = None,
        sleep_hours: float | None = None,
        readiness: int | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Blocked until HabitTracker has a daily check-in or health-log schema."""
        _ = (weight, sleep_hours, readiness, note)
        return blocked_checkin_response()

