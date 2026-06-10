"""Dashboard composition."""

from __future__ import annotations

from typing import Any

from poke_mcp.services.habittracker_service import HabitTrackerService


class DashboardService:
    def __init__(self, habittracker_service: HabitTrackerService) -> None:
        self._habittracker_service = habittracker_service

    def get_today_dashboard(self) -> dict[str, Any]:
        today = self._habittracker_service.list_today_habits()
        habits = today["habits"]
        completed = [habit for habit in habits if habit["completed"]]
        incomplete = [habit for habit in habits if not habit["completed"]]
        return {
            "date": today["date"],
            "completed_count": len(completed),
            "total_count": len(habits),
            "completed_habits": completed,
            "incomplete_habits": incomplete,
        }

