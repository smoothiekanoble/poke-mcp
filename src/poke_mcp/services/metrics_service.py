"""Read-only HabitTracker metric queries (daily_metrics / metric_events)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from poke_mcp.config import Settings
from poke_mcp.services.habittracker_service import MissingConfigurationError

BODY_WEIGHT_METRIC = "body_weight"
MAX_WINDOW_DAYS = 3650

DAILY_METRIC_COLUMNS = "metric_date,metric_type,value,unit,source"
METRIC_EVENT_COLUMNS = "occurred_at,metric_date,metric_type,value,unit,source,source_detail"


def _invalid_days_response(days: int) -> dict[str, Any]:
    return {
        "status": "invalid_request",
        "message": f"days must be between 1 and {MAX_WINDOW_DAYS}, got {days}.",
    }


def _date_value_point(row: dict[str, Any]) -> dict[str, Any]:
    return {"date": str(row["metric_date"]), "value": float(row["value"])}


class MetricsService:
    """Read-only access to imported HabitTracker metrics, scoped to Daniel's user."""

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

    def get_latest_body_weight(self) -> dict[str, Any]:
        user_id = self._require_user_id()
        response = (
            self._supabase.table("daily_metrics")
            .select(DAILY_METRIC_COLUMNS)
            .eq("user_id", user_id)
            .eq("metric_type", BODY_WEIGHT_METRIC)
            .order("metric_date", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return self._no_data_response(BODY_WEIGHT_METRIC)

        daily = rows[0]
        return {
            "status": "ok",
            "metric_type": BODY_WEIGHT_METRIC,
            "date": str(daily["metric_date"]),
            "value": float(daily["value"]),
            "unit": daily.get("unit"),
            "source": daily.get("source"),
            "latest_event": self._latest_event(user_id, BODY_WEIGHT_METRIC),
        }

    def get_body_weight_history(self, days: int = 90) -> dict[str, Any]:
        return self._history(BODY_WEIGHT_METRIC, days)

    def get_body_weight_trend(self, days: int = 30) -> dict[str, Any]:
        return self._summary(BODY_WEIGHT_METRIC, days)

    def get_metric_summary(self, metric_type: str, days: int = 30) -> dict[str, Any]:
        metric_type = metric_type.strip()
        if not metric_type:
            return {
                "status": "invalid_request",
                "message": "metric_type is required.",
            }
        return self._summary(metric_type, days)

    def _history(self, metric_type: str, days: int) -> dict[str, Any]:
        if not 1 <= days <= MAX_WINDOW_DAYS:
            return _invalid_days_response(days)
        start_date, end_date = self._window(days)
        rows = self._daily_metrics_in_range(metric_type, start_date, end_date)
        if not rows:
            return self._no_data_response(metric_type, days, start_date, end_date)
        return {
            "status": "ok",
            "metric_type": metric_type,
            "days": days,
            "start_date": start_date,
            "end_date": end_date,
            "count": len(rows),
            "unit": rows[-1].get("unit"),
            "entries": [
                {
                    "date": str(row["metric_date"]),
                    "value": float(row["value"]),
                    "unit": row.get("unit"),
                    "source": row.get("source"),
                }
                for row in rows
            ],
        }

    def _summary(self, metric_type: str, days: int) -> dict[str, Any]:
        if not 1 <= days <= MAX_WINDOW_DAYS:
            return _invalid_days_response(days)
        start_date, end_date = self._window(days)
        rows = self._daily_metrics_in_range(metric_type, start_date, end_date)
        if not rows:
            return self._no_data_response(metric_type, days, start_date, end_date)

        values = [float(row["value"]) for row in rows]
        first = _date_value_point(rows[0])
        latest = _date_value_point(rows[-1])
        min_row = min(rows, key=lambda row: float(row["value"]))
        max_row = max(rows, key=lambda row: float(row["value"]))
        return {
            "status": "ok",
            "metric_type": metric_type,
            "days": days,
            "start_date": start_date,
            "end_date": end_date,
            "data_points": len(rows),
            "unit": rows[-1].get("unit"),
            "first": first,
            "latest": latest,
            "min": _date_value_point(min_row),
            "max": _date_value_point(max_row),
            "average": round(sum(values) / len(values), 2),
            "change": round(latest["value"] - first["value"], 2),
        }

    def _daily_metrics_in_range(
        self,
        metric_type: str,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        user_id = self._require_user_id()
        response = (
            self._supabase.table("daily_metrics")
            .select(DAILY_METRIC_COLUMNS)
            .eq("user_id", user_id)
            .eq("metric_type", metric_type)
            .gte("metric_date", start_date)
            .lte("metric_date", end_date)
            .order("metric_date", desc=False)
            .execute()
        )
        return [dict(row) for row in response.data or []]

    def _latest_event(self, user_id: str, metric_type: str) -> dict[str, Any] | None:
        response = (
            self._supabase.table("metric_events")
            .select(METRIC_EVENT_COLUMNS)
            .eq("user_id", user_id)
            .eq("metric_type", metric_type)
            .order("occurred_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None
        event = rows[0]
        return {
            "occurred_at": str(event["occurred_at"]),
            "value": float(event["value"]),
            "unit": event.get("unit"),
            "source": event.get("source"),
            "source_detail": event.get("source_detail"),
        }

    def _window(self, days: int) -> tuple[str, str]:
        end = datetime.fromisoformat(self.today_ymd()).date()
        start = end - timedelta(days=days - 1)
        return start.isoformat(), end.isoformat()

    def _no_data_response(
        self,
        metric_type: str,
        days: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        if days is None:
            message = f"No {metric_type} data found."
        else:
            message = (
                f"No {metric_type} data found between {start_date} and {end_date}."
            )
        payload: dict[str, Any] = {
            "status": "no_data",
            "metric_type": metric_type,
            "message": message,
        }
        if days is not None:
            payload.update({"days": days, "start_date": start_date, "end_date": end_date})
        return payload

    def _require_user_id(self) -> str:
        if not self._settings.daniel_user_id:
            raise MissingConfigurationError("DANIEL_USER_ID is required")
        return self._settings.daniel_user_id
