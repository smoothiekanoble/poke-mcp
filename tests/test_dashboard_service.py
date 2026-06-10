from poke_mcp.config import Settings
from poke_mcp.services.dashboard_service import DashboardService
from poke_mcp.services.habittracker_service import HabitTrackerService
from tests.fakes import FakeSupabase


def test_dashboard_summarizes_today_habits() -> None:
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
            ],
            "habit_logs": [
                {"habit_id": "h1", "date": "2026-06-09", "completed": True},
            ],
        }
    )
    settings = Settings(daniel_user_id="user-1", _env_file=None)
    service = HabitTrackerService(fake, settings, today_provider=lambda: "2026-06-09")

    dashboard = DashboardService(service).get_today_dashboard()

    assert dashboard["date"] == "2026-06-09"
    assert dashboard["completed_count"] == 1
    assert dashboard["total_count"] == 2
    assert [habit["title"] for habit in dashboard["completed_habits"]] == ["Cardio"]
    assert [habit["title"] for habit in dashboard["incomplete_habits"]] == ["Creatine"]

