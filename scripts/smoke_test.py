"""Manual smoke test for the local or deployed Poke MCP server.

Read-only by default. Real Supabase writes require --write and --habit.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from fastmcp import Client

from poke_mcp.config import Settings
from poke_mcp.server import create_mcp
from poke_mcp.services.habittracker_service import normalize_habit_name

EXPECTED_TOOLS = {
    "health",
    "list_today_habits",
    "complete_habit",
    "uncomplete_habit",
    "get_today_dashboard",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a local MCP smoke test. Read-only unless --write is supplied. "
            "Write mode updates today's habit_logs through real Supabase."
        )
    )
    parser.add_argument(
        "--url",
        help=(
            "Public or local MCP URL to smoke test over HTTP, for example "
            "https://your-host.example.com/mcp. If omitted, the script uses "
            "an in-process local FastMCP client."
        ),
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Intentionally call complete_habit and uncomplete_habit against real Supabase. "
            "Requires --habit."
        ),
    )
    parser.add_argument(
        "--habit",
        help=(
            "Habit title to use for --write. If the habit starts incomplete, write mode "
            "leaves it incomplete but may create a completed=false log row."
        ),
    )
    return parser.parse_args()


def print_json(label: str, payload: Any) -> None:
    print(f"\n== {label} ==")
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


async def call_tool(client: Client, name: str, arguments: dict[str, Any] | None = None) -> Any:
    result = await client.call_tool(name, arguments or {})
    return result.data


def choose_write_sequence(
    habits: list[dict[str, Any]],
    habit_name: str,
) -> list[tuple[str, str]]:
    query = habit_name.strip()
    exact = [habit for habit in habits if habit.get("title") == query]
    if len(exact) > 1:
        raise ValueError(f"Multiple exact matches for '{habit_name}'; choose a unique title.")
    if len(exact) == 1:
        matched = exact[0]
    else:
        normalized_query = normalize_habit_name(query)
        normalized = [
            habit
            for habit in habits
            if normalize_habit_name(str(habit.get("title", ""))) == normalized_query
        ]
        if len(normalized) > 1:
            raise ValueError(
                f"Multiple normalized matches for '{habit_name}'; choose a unique title."
            )
        if not normalized:
            raise ValueError(f"No active habit matched '{habit_name}'.")
        matched = normalized[0]

    # Exercise both write tools while ending on the same visible completion state.
    if matched.get("completed"):
        return [("uncomplete_habit", "mark incomplete"), ("complete_habit", "restore complete")]
    return [("complete_habit", "mark complete"), ("uncomplete_habit", "restore incomplete")]


async def run(args: argparse.Namespace) -> int:
    if args.write and not args.habit:
        print("--write requires --habit \"Habit title\".", file=sys.stderr)
        return 2

    settings = Settings()
    transport = args.url or create_mcp(settings=settings)

    async with Client(transport) as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        missing = sorted(EXPECTED_TOOLS - tool_names)
        print_json("registered_tools", sorted(tool_names))
        if missing:
            print_json("missing_expected_tools", missing)
            return 1

        health = await call_tool(client, "health")
        print_json("health", health)

        supabase_available = bool(health.get("supabase_configured"))
        if not args.url and not settings.supabase_configured:
            supabase_available = False

        if not supabase_available:
            print_json(
                "supabase_skipped",
                {
                    "reason": (
                        "The target server reports Supabase is not fully configured. "
                        "Set SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and DANIEL_USER_ID "
                        "on that target to call real HabitTracker data."
                    ),
                    "write_requested": args.write,
                },
            )
            return 0 if not args.write else 2

        today_habits = await call_tool(client, "list_today_habits")
        print_json("list_today_habits", today_habits)

        dashboard = await call_tool(client, "get_today_dashboard")
        print_json("get_today_dashboard", dashboard)

        if not args.write:
            print_json(
                "write_tools_skipped",
                {
                    "reason": "complete_habit and uncomplete_habit are write tools.",
                    "run_intentionally": (
                        r'.\.venv\Scripts\python scripts\smoke_test.py --write '
                        r'--habit "Habit title"'
                    ),
                },
            )
            return 0

        habits = list(today_habits.get("habits") or [])
        sequence = choose_write_sequence(habits, args.habit)
        for tool_name, label in sequence:
            payload = await call_tool(client, tool_name, {"habit_name": args.habit})
            print_json(f"{tool_name}_{label.replace(' ', '_')}", payload)

        print_json("dashboard_after_write_smoke", await call_tool(client, "get_today_dashboard"))
        return 0


def main() -> None:
    raise SystemExit(asyncio.run(run(parse_args())))


if __name__ == "__main__":
    main()
