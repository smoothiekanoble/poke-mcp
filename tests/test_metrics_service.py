from poke_mcp.config import Settings
from poke_mcp.services.metrics_service import MetricsService
from tests.fakes import FakeSupabase

TODAY = "2026-06-09"


def settings() -> Settings:
    return Settings(daniel_user_id="user-1", _env_file=None)


def service(fake: FakeSupabase) -> MetricsService:
    return MetricsService(fake, settings(), today_provider=lambda: TODAY)


def daily_metric(
    metric_date: str,
    value: float,
    *,
    user_id: str = "user-1",
    metric_type: str = "body_weight",
) -> dict[str, object]:
    return {
        "user_id": user_id,
        "metric_date": metric_date,
        "metric_type": metric_type,
        "value": value,
        "unit": "lb",
        "source": "medm_health",
    }


def test_get_latest_body_weight_returns_latest_daily_and_event() -> None:
    fake = FakeSupabase(
        {
            "daily_metrics": [
                daily_metric("2026-06-05", 161.2),
                daily_metric("2026-06-06", 159.8),
                daily_metric("2026-06-06", 180.0, user_id="other-user"),
            ],
            "metric_events": [
                {
                    "user_id": "user-1",
                    "occurred_at": "2026-06-06T15:37:38+00:00",
                    "metric_date": "2026-06-06",
                    "metric_type": "body_weight",
                    "value": 159.8,
                    "unit": "lb",
                    "source": "medm_health",
                    "source_detail": "Smart Weight Scale 208B3",
                },
                {
                    "user_id": "user-1",
                    "occurred_at": "2026-06-05T23:37:54+00:00",
                    "metric_date": "2026-06-05",
                    "metric_type": "body_weight",
                    "value": 161.2,
                    "unit": "lb",
                    "source": "medm_health",
                    "source_detail": "Smart Weight Scale 208B3",
                },
            ],
        }
    )

    result = service(fake).get_latest_body_weight()

    assert result == {
        "status": "ok",
        "metric_type": "body_weight",
        "date": "2026-06-06",
        "value": 159.8,
        "unit": "lb",
        "source": "medm_health",
        "latest_event": {
            "occurred_at": "2026-06-06T15:37:38+00:00",
            "value": 159.8,
            "unit": "lb",
            "source": "medm_health",
            "source_detail": "Smart Weight Scale 208B3",
        },
    }
    assert all(operation["action"] == "select" for operation in fake.operations)
    assert all(
        ("eq", "user_id", "user-1") in operation["filters"] for operation in fake.operations
    )


def test_get_latest_body_weight_without_events_returns_none_event() -> None:
    fake = FakeSupabase({"daily_metrics": [daily_metric("2026-06-06", 159.8)]})

    result = service(fake).get_latest_body_weight()

    assert result["status"] == "ok"
    assert result["latest_event"] is None


def test_get_latest_body_weight_no_data() -> None:
    fake = FakeSupabase({"daily_metrics": [], "metric_events": []})

    result = service(fake).get_latest_body_weight()

    assert result["status"] == "no_data"
    assert result["metric_type"] == "body_weight"
    assert all(operation["table"] != "metric_events" for operation in fake.operations)


def test_get_body_weight_history_filters_window_and_orders_ascending() -> None:
    fake = FakeSupabase(
        {
            "daily_metrics": [
                daily_metric("2026-06-06", 159.8),
                daily_metric("2026-06-02", 158.5),
                daily_metric("2025-01-01", 150.0),
                daily_metric("2026-06-05", 161.2, user_id="other-user"),
                daily_metric("2026-06-05", 7.5, metric_type="sleep_hours"),
            ]
        }
    )

    result = service(fake).get_body_weight_history(days=90)

    assert result["status"] == "ok"
    assert result["days"] == 90
    assert result["start_date"] == "2026-03-12"
    assert result["end_date"] == TODAY
    assert result["count"] == 2
    assert result["unit"] == "lb"
    assert result["entries"] == [
        {"date": "2026-06-02", "value": 158.5, "unit": "lb", "source": "medm_health"},
        {"date": "2026-06-06", "value": 159.8, "unit": "lb", "source": "medm_health"},
    ]


def test_get_body_weight_history_no_data() -> None:
    fake = FakeSupabase({"daily_metrics": [daily_metric("2025-01-01", 150.0)]})

    result = service(fake).get_body_weight_history(days=30)

    assert result == {
        "status": "no_data",
        "metric_type": "body_weight",
        "message": "No body_weight data found between 2026-05-11 and 2026-06-09.",
        "days": 30,
        "start_date": "2026-05-11",
        "end_date": TODAY,
    }


def test_get_body_weight_history_rejects_invalid_days() -> None:
    fake = FakeSupabase()

    result = service(fake).get_body_weight_history(days=0)

    assert result["status"] == "invalid_request"
    assert fake.operations == []


def test_get_body_weight_trend_computes_stats() -> None:
    fake = FakeSupabase(
        {
            "daily_metrics": [
                daily_metric("2026-06-02", 158.5),
                daily_metric("2026-06-05", 160.5),
                daily_metric("2026-06-06", 159.8),
                daily_metric("2026-05-20", 162.0),
            ]
        }
    )

    result = service(fake).get_body_weight_trend(days=30)

    assert result["status"] == "ok"
    assert result["metric_type"] == "body_weight"
    assert result["days"] == 30
    assert result["start_date"] == "2026-05-11"
    assert result["end_date"] == TODAY
    assert result["data_points"] == 4
    assert result["unit"] == "lb"
    assert result["first"] == {"date": "2026-05-20", "value": 162.0}
    assert result["latest"] == {"date": "2026-06-06", "value": 159.8}
    assert result["min"] == {"date": "2026-06-02", "value": 158.5}
    assert result["max"] == {"date": "2026-05-20", "value": 162.0}
    assert result["average"] == 160.2
    assert result["change"] == -2.2


def test_get_body_weight_trend_no_data() -> None:
    fake = FakeSupabase()

    result = service(fake).get_body_weight_trend(days=30)

    assert result["status"] == "no_data"
    assert result["days"] == 30


def test_get_metric_summary_generic_metric() -> None:
    fake = FakeSupabase(
        {
            "daily_metrics": [
                daily_metric("2026-06-05", 7.5, metric_type="sleep_hours"),
                daily_metric("2026-06-06", 8.0, metric_type="sleep_hours"),
                daily_metric("2026-06-06", 159.8),
            ]
        }
    )

    result = service(fake).get_metric_summary("sleep_hours", days=30)

    assert result["status"] == "ok"
    assert result["metric_type"] == "sleep_hours"
    assert result["data_points"] == 2
    assert result["first"] == {"date": "2026-06-05", "value": 7.5}
    assert result["latest"] == {"date": "2026-06-06", "value": 8.0}
    assert result["average"] == 7.75
    assert result["change"] == 0.5


def test_get_metric_summary_requires_metric_type() -> None:
    fake = FakeSupabase()

    result = service(fake).get_metric_summary("   ", days=30)

    assert result["status"] == "invalid_request"
    assert fake.operations == []


def test_get_metric_summary_no_data() -> None:
    fake = FakeSupabase()

    result = service(fake).get_metric_summary("body_fat_pct", days=30)

    assert result["status"] == "no_data"
    assert result["metric_type"] == "body_fat_pct"
