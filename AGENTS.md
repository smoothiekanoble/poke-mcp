# Agent Notes

This repo is Daniel's private Poke tool hub / Daniel OS MCP server.

## Source Of Truth

- HabitTracker repo: `C:\dev\personal\habittracker`
- HabitTracker Supabase is the data source for habits.
- This repo talks directly to Supabase for the MVP through narrow service functions.
- Do not add HabitTracker API routes from this repo.

## Safety Rules

- Never commit `.env`, credentials, tokens, logs, or service role keys.
- `SUPABASE_SERVICE_ROLE_KEY` is server-side only.
- Every Supabase operation must be scoped to `DANIEL_USER_ID` or to habit IDs first resolved from Daniel's habits.
- Do not expose raw SQL tools, generic table update tools, delete tools, or local shell/Codex execution tools.
- MCP tool functions should be thin; business logic belongs in `src/poke_mcp/services/`.

## MVP Scope

The current MVP is habit tracking first:

- List today's active habits.
- Complete a habit for today.
- Mark a habit incomplete for today without deleting rows.
- Return today's habit dashboard.

Tasks, check-ins, and calendar integration are future work after explicit schema/integration setup. Do not register placeholder/stub tools for them; only working tools belong in the MCP surface (always-"blocked" stubs caused Poke to misdiagnose the server).

## Commands

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python scripts\smoke_test.py
.\.venv\Scripts\python -m poke_mcp.server
```

Use `.\.venv\Scripts\python scripts\smoke_test.py --write --habit "Habit title"` only when Daniel explicitly wants a real Supabase write smoke test.
For remote protected smoke tests, use `.\.venv\Scripts\python scripts\smoke_test.py --url https://host.example.com/mcp --api-key "<secret>"`; this sends `Authorization: Bearer <secret>` through FastMCP's HTTP client auth.

## Deployment Notes

- Deployment files are `Dockerfile`, `render.yaml`, `railway.toml`, and `fly.toml`.
- The server must bind to `MCP_HOST=0.0.0.0` on public hosts.
- The server uses `MCP_PORT`, or platform `PORT` when `MCP_PORT` is absent.
- The MCP endpoint must stay at `MCP_PATH` unless Daniel changes the Poke integration URL.
- When `POKE_MCP_API_KEY` is set, `/mcp` requires `Authorization: Bearer <POKE_MCP_API_KEY>`.
- `/health` is for platform health checks and must stay secret-safe.
- Do not put Supabase secrets in deployment config files; set them in the host secret/env UI.
