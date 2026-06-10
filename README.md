# Poke HabitTracker MCP

This is Daniel's private Poke-compatible MCP server. The MVP lets Poke read and update today's HabitTracker habits directly through Supabase.

## Architecture

```text
Poke / Telegram / SMS
        |
FastMCP server in this repo
        |
Supabase HabitTracker tables
        |
HabitTracker web/iOS clients
```

HabitTracker remains the source of truth. This server does not add API routes to HabitTracker and does not create schema migrations.

## Current Tools

- `health()`: returns safe server/config status without secrets.
- `list_today_habits()`: lists active habits for today with completion status.
- `complete_habit(habit_name)`: marks today's matching habit complete.
- `uncomplete_habit(habit_name)`: marks today's matching habit incomplete without deleting rows.
- `get_today_dashboard()`: returns completed/incomplete habit summary for today.
- Task and check-in tools return blocked responses until HabitTracker has those schemas.

## Environment

Copy `.env.example` to `.env` and fill:

```text
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
DANIEL_USER_ID=
```

Optional:

```text
APP_ENV=development
APP_TIMEZONE=America/Chicago
POKE_MCP_API_KEY=
```

`SUPABASE_SERVICE_ROLE_KEY` must stay server-side. Every operation in this repo is scoped to `DANIEL_USER_ID`.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Run tests and lint:

```powershell
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
```

Run the MCP server locally:

```powershell
.\.venv\Scripts\python -m poke_mcp.server
```

The server uses FastMCP HTTP transport at `/mcp`.

## HabitTracker Schema Assumptions

The MVP only uses:

- `habits`: `id`, `user_id`, `title`, `active_from`, `active_until`, `created_at`
- `habit_logs`: `habit_id`, `date`, `completed`

Active habits are those where `active_from <= today` and `active_until` is null or after today. Missing `active_from` falls back to `created_at`, matching HabitTracker's app logic.

## Known Limitations

- No task tools until HabitTracker gets a task table.
- No check-in tools until HabitTracker gets a daily check-in or health-log table.
- No Google Calendar integration in this MVP.
- `uncomplete_habit` upserts `completed=false`; HabitTracker web currently often represents incomplete as no log row.
- Production remote auth should be finalized when Poke custom integration requirements are known.

