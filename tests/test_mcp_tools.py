from fastmcp import Client

from poke_mcp.config import Settings
from poke_mcp.server import create_mcp
from tests.fakes import FakeSupabase


async def test_mcp_registers_health_and_habit_tool() -> None:
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
            "habit_logs": [{"habit_id": "h1", "date": "2026-06-09", "completed": True}],
        }
    )
    settings = Settings(daniel_user_id="user-1", _env_file=None)
    mcp = create_mcp(settings=settings, supabase_client=fake, today_provider=lambda: "2026-06-09")

    async with Client(mcp) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools}

        assert "health" in names
        assert "list_today_habits" in names

        health = await client.call_tool("health", {})
        habits = await client.call_tool("list_today_habits", {})

    assert health.data["status"] == "ok"
    assert habits.data["habits"] == [
        {"id": "h1", "title": "Cardio", "date": "2026-06-09", "completed": True}
    ]

