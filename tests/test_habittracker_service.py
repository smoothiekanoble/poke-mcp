from poke_mcp.config import Settings
from poke_mcp.services.habittracker_service import (
    HabitTrackerService,
    normalize_habit_name,
)
from tests.fakes import FakeSupabase

TODAY = "2026-06-09"


def settings() -> Settings:
    return Settings(daniel_user_id="user-1", _env_file=None)


def service(fake: FakeSupabase) -> HabitTrackerService:
    return HabitTrackerService(fake, settings(), today_provider=lambda: TODAY)


def test_normalize_habit_name_casefolds_and_collapses_spaces() -> None:
    assert normalize_habit_name("  Drink   WATER ") == "drink water"


def test_list_today_habits_filters_active_and_composes_logs() -> None:
    fake = FakeSupabase(
        {
            "habits": [
                {
                    "id": "h1",
                    "user_id": "user-1",
                    "title": "Cardio",
                    "active_from": "2026-06-01",
                    "active_until": None,
                    "created_at": "2026-06-01T00:00:00Z",
                },
                {
                    "id": "h2",
                    "user_id": "user-1",
                    "title": "Creatine",
                    "active_from": "2026-06-01",
                    "active_until": None,
                    "created_at": "2026-06-01T00:00:01Z",
                },
                {
                    "id": "h3",
                    "user_id": "user-1",
                    "title": "Old Habit",
                    "active_from": "2026-06-01",
                    "active_until": "2026-06-08",
                    "created_at": "2026-06-01T00:00:02Z",
                },
                {
                    "id": "h4",
                    "user_id": "user-1",
                    "title": "Future Habit",
                    "active_from": "2026-06-10",
                    "active_until": None,
                    "created_at": "2026-06-01T00:00:03Z",
                },
                {
                    "id": "h5",
                    "user_id": "other-user",
                    "title": "Other User",
                    "active_from": "2026-06-01",
                    "active_until": None,
                    "created_at": "2026-06-01T00:00:04Z",
                },
            ],
            "habit_logs": [
                {"habit_id": "h1", "date": TODAY, "completed": True},
                {"habit_id": "h2", "date": TODAY, "completed": False},
            ],
        }
    )

    result = service(fake).list_today_habits()

    assert result["date"] == TODAY
    assert result["habits"] == [
        {"id": "h1", "title": "Cardio", "date": TODAY, "completed": True},
        {"id": "h2", "title": "Creatine", "date": TODAY, "completed": False},
    ]
    assert fake.operations[0]["filters"] == [("eq", "user_id", "user-1")]
    assert ("in", "habit_id", ["h1", "h2"]) in fake.operations[1]["filters"]


def test_complete_habit_exact_match_upserts_true() -> None:
    fake = FakeSupabase(
        {
            "habits": [
                {
                    "id": "h1",
                    "user_id": "user-1",
                    "title": "Cardio",
                    "active_from": "2026-06-01",
                    "active_until": None,
                    "created_at": "2026-06-01T00:00:00Z",
                }
            ],
            "habit_logs": [],
        }
    )

    result = service(fake).complete_habit("Cardio")

    assert result["status"] == "completed"
    assert result["completed"] is True
    assert fake.operations[-1] == {
        "action": "upsert",
        "table": "habit_logs",
        "payload": {"habit_id": "h1", "date": TODAY, "completed": True},
        "on_conflict": "habit_id,date",
    }


def test_uncomplete_habit_normalized_match_upserts_false() -> None:
    fake = FakeSupabase(
        {
            "habits": [
                {
                    "id": "h1",
                    "user_id": "user-1",
                    "title": "Drink  Water",
                    "active_from": "2026-06-01",
                    "active_until": None,
                    "created_at": "2026-06-01T00:00:00Z",
                }
            ],
            "habit_logs": [],
        }
    )

    result = service(fake).uncomplete_habit(" drink water ")

    assert result["status"] == "uncompleted"
    assert result["completed"] is False
    assert fake.operations[-1]["payload"] == {
        "habit_id": "h1",
        "date": TODAY,
        "completed": False,
    }


def test_multiple_normalized_matches_returns_candidates_without_upsert() -> None:
    fake = FakeSupabase(
        {
            "habits": [
                {
                    "id": "h1",
                    "user_id": "user-1",
                    "title": "Cardio",
                    "active_from": "2026-06-01",
                    "active_until": None,
                    "created_at": "2026-06-01T00:00:00Z",
                },
                {
                    "id": "h2",
                    "user_id": "user-1",
                    "title": "cardio ",
                    "active_from": "2026-06-01",
                    "active_until": None,
                    "created_at": "2026-06-01T00:00:01Z",
                },
            ],
            "habit_logs": [],
        }
    )

    result = service(fake).complete_habit("CARDIO")

    assert result["status"] == "multiple_matches"
    assert result["candidates"] == [
        {"id": "h1", "title": "Cardio"},
        {"id": "h2", "title": "cardio "},
    ]
    assert all(operation["action"] != "upsert" for operation in fake.operations)


def test_no_match_returns_candidates_without_upsert() -> None:
    fake = FakeSupabase(
        {
            "habits": [
                {
                    "id": "h1",
                    "user_id": "user-1",
                    "title": "Cardio",
                    "active_from": "2026-06-01",
                    "active_until": None,
                    "created_at": "2026-06-01T00:00:00Z",
                }
            ],
            "habit_logs": [],
        }
    )

    result = service(fake).complete_habit("Creatine")

    assert result["status"] == "no_match"
    assert result["candidates"] == [{"id": "h1", "title": "Cardio"}]
    assert all(operation["action"] != "upsert" for operation in fake.operations)

