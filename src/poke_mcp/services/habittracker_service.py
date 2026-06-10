"""HabitTracker Supabase business logic."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from poke_mcp.config import Settings


class MissingConfigurationError(RuntimeError):
    """Raised when required server-side configuration is missing."""


@dataclass(frozen=True)
class HabitCandidate:
    id: str
    title: str

    def as_dict(self) -> dict[str, str]:
        return {"id": self.id, "title": self.title}


def normalize_habit_name(value: str) -> str:
    return " ".join(value.casefold().split())


def _date_prefix(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:10]


def _habit_active_on(habit: dict[str, Any], date_ymd: str) -> bool:
    active_from = _date_prefix(habit.get("active_from")) or _date_prefix(habit.get("created_at"))
    active_until = _date_prefix(habit.get("active_until"))
    if active_from and date_ymd < active_from:
        return False
    if active_until and date_ymd > active_until:
        return False
    return True


class HabitTrackerService:
    def __init__(
        self,
        supabase: Any,
        settings: Settings,
        today_provider: Callable[[], str] | None = None,
    ) -> None:
        self._supabase = supabase
        self._settings = settings
        self._today_provider = today_provider

    def today_ymd(self) -> str:
        if self._today_provider:
            return self._today_provider()
        return datetime.now(self._settings.timezone()).date().isoformat()

    def list_today_habits(self) -> dict[str, Any]:
        date_ymd = self.today_ymd()
        habits = self._active_habits_for_date(date_ymd)
        logs = self._logs_for_habits_on_date([habit["id"] for habit in habits], date_ymd)
        completed_by_habit_id = {
            str(log["habit_id"]): bool(log.get("completed"))
            for log in logs
            if _date_prefix(log.get("date")) == date_ymd
        }
        return {
            "date": date_ymd,
            "habits": [
                {
                    "id": str(habit["id"]),
                    "title": str(habit["title"]),
                    "date": date_ymd,
                    "completed": completed_by_habit_id.get(str(habit["id"]), False),
                }
                for habit in habits
            ],
        }

    def complete_habit(self, habit_name: str) -> dict[str, Any]:
        return self._set_habit_completion(habit_name, completed=True)

    def uncomplete_habit(self, habit_name: str) -> dict[str, Any]:
        return self._set_habit_completion(habit_name, completed=False)

    def _set_habit_completion(self, habit_name: str, *, completed: bool) -> dict[str, Any]:
        date_ymd = self.today_ymd()
        match = self._match_active_habit(habit_name, date_ymd)
        if match["status"] != "matched":
            return match

        habit = match["habit"]
        payload = {
            "habit_id": str(habit["id"]),
            "date": date_ymd,
            "completed": completed,
        }
        (
            self._supabase.table("habit_logs")
            .upsert(payload, on_conflict="habit_id,date")
            .execute()
        )

        status = "completed" if completed else "uncompleted"
        readable = "complete" if completed else "incomplete"
        return {
            "status": status,
            "message": f"Marked {habit['title']} {readable} for {date_ymd}.",
            "habit": HabitCandidate(id=str(habit["id"]), title=str(habit["title"])).as_dict(),
            "date": date_ymd,
            "completed": completed,
        }

    def _match_active_habit(self, habit_name: str, date_ymd: str) -> dict[str, Any]:
        query_name = habit_name.strip()
        if not query_name:
            return {
                "status": "no_match",
                "message": "Habit name is required.",
                "date": date_ymd,
                "candidates": [],
            }

        habits = self._active_habits_for_date(date_ymd)
        exact = [habit for habit in habits if str(habit.get("title")) == query_name]
        if len(exact) == 1:
            return {"status": "matched", "habit": exact[0], "date": date_ymd}
        if len(exact) > 1:
            return self._multiple_matches(query_name, exact, date_ymd)

        normalized_query = normalize_habit_name(query_name)
        normalized = [
            habit
            for habit in habits
            if normalize_habit_name(str(habit.get("title", ""))) == normalized_query
        ]
        if len(normalized) == 1:
            return {"status": "matched", "habit": normalized[0], "date": date_ymd}
        if len(normalized) > 1:
            return self._multiple_matches(query_name, normalized, date_ymd)

        return {
            "status": "no_match",
            "message": f"No active habit matched '{query_name}' for {date_ymd}.",
            "date": date_ymd,
            "candidates": [
                HabitCandidate(id=str(habit["id"]), title=str(habit["title"])).as_dict()
                for habit in habits
            ],
        }

    def _multiple_matches(
        self,
        habit_name: str,
        habits: list[dict[str, Any]],
        date_ymd: str,
    ) -> dict[str, Any]:
        return {
            "status": "multiple_matches",
            "message": f"Multiple active habits matched '{habit_name}'. Choose one exactly.",
            "date": date_ymd,
            "candidates": [
                HabitCandidate(id=str(habit["id"]), title=str(habit["title"])).as_dict()
                for habit in habits
            ],
        }

    def _active_habits_for_date(self, date_ymd: str) -> list[dict[str, Any]]:
        user_id = self._require_user_id()
        response = (
            self._supabase.table("habits")
            .select("id,user_id,title,active_from,active_until,created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
        )
        rows = response.data or []
        return [
            dict(row)
            for row in rows
            if str(row.get("user_id")) == user_id and _habit_active_on(dict(row), date_ymd)
        ]

    def _logs_for_habits_on_date(
        self,
        habit_ids: list[str],
        date_ymd: str,
    ) -> list[dict[str, Any]]:
        if not habit_ids:
            return []
        response = (
            self._supabase.table("habit_logs")
            .select("habit_id,date,completed")
            .eq("date", date_ymd)
            .in_("habit_id", habit_ids)
            .execute()
        )
        return [dict(row) for row in response.data or []]

    def _require_user_id(self) -> str:
        if not self._settings.daniel_user_id:
            raise MissingConfigurationError("DANIEL_USER_ID is required")
        return self._settings.daniel_user_id

