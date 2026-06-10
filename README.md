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

Create `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Fill the required HabitTracker Supabase values:

```text
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
DANIEL_USER_ID=
```

Optional:

```text
APP_ENV=development
APP_TIMEZONE=America/Chicago
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_PATH=/mcp
POKE_MCP_API_KEY=
```

`SUPABASE_SERVICE_ROLE_KEY` must stay server-side. Every operation in this repo is scoped to `DANIEL_USER_ID`.

`POKE_MCP_API_KEY` is a reserved config surface and is reported by `health()`, but this MVP does not yet enforce an API-key header at the FastMCP HTTP transport. Do not treat it as endpoint protection until auth is wired or the deployment host/proxy enforces it.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

## Run Tests

Run unit tests and lint:

```powershell
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
```

## Run The Server

Run the MCP server locally:

```powershell
.\.venv\Scripts\python -m poke_mcp.server
```

The default local MCP URL is:

```text
http://127.0.0.1:8000/mcp
```

The server uses FastMCP HTTP transport at `MCP_PATH`, default `/mcp`.

## Manual Smoke Tests

The smoke script uses an in-memory FastMCP client. It always checks tool registration and `health()`. It calls real Supabase read tools only when `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `DANIEL_USER_ID` are present.

Read-only smoke test:

```powershell
.\.venv\Scripts\python scripts\smoke_test.py
```

When env vars are present, the read-only smoke test calls:

- `health()`
- `list_today_habits()`
- `get_today_dashboard()`

Intentional write smoke test:

```powershell
.\.venv\Scripts\python scripts\smoke_test.py --write --habit "Creatine"
```

Write mode calls both `complete_habit()` and `uncomplete_habit()` against real Supabase. It chooses the order so the habit ends with the same visible completed/incomplete state it had at the start. If the habit starts incomplete, this may create a `completed=false` `habit_logs` row because this MVP intentionally does not delete logs.

## Deploy To HTTPS

Use a host that can run Python 3.12 and expose HTTPS, such as Render, Railway, or Fly.io. This repo includes:

- `Dockerfile`: production container image.
- `render.yaml`: Render Blueprint for a Docker web service.
- `railway.toml`: Railway config-as-code using the Dockerfile.
- `fly.toml`: Fly app config using the Dockerfile.

Runtime behavior:

- The server binds `MCP_HOST`, default `127.0.0.1`.
- The server uses `MCP_PORT`; if `MCP_PORT` is absent, platform `PORT` is accepted.
- The MCP endpoint is mounted at `MCP_PATH`, default `/mcp`.
- `/health` is a plain HTTP health route for deployment checks. It is secret-safe and returns the same config booleans as the `health()` MCP tool.

Recommended deployment shape:

```text
Build/install: python -m pip install -e .
Start: python -m poke_mcp.server
Environment:
  APP_ENV=production
  MCP_HOST=0.0.0.0
  MCP_PORT=<numeric platform port; PORT is also accepted>
  MCP_PATH=/mcp
  SUPABASE_URL=<project url>
  SUPABASE_SERVICE_ROLE_KEY=<server-side secret>
  DANIEL_USER_ID=<Daniel's auth.users id>
```

Terminate TLS at the hosting provider and connect Poke to:

```text
https://your-public-host.example.com/mcp
```

Do not expose the endpoint publicly without either FastMCP transport auth or a host/proxy rule that enforces a secret header. The current `POKE_MCP_API_KEY` helper is not transport enforcement.

### Render

Use `render.yaml` as a Blueprint, or create a Docker web service from the GitHub repo.

Set these secret/env values in Render:

```text
APP_ENV=production
APP_TIMEZONE=America/Chicago
MCP_HOST=0.0.0.0
MCP_PATH=/mcp
SUPABASE_URL=<project url>
SUPABASE_SERVICE_ROLE_KEY=<server-side secret>
DANIEL_USER_ID=<Daniel's auth.users id>
```

Render provides `PORT`, so `MCP_PORT` is optional. Health check path: `/health`.

### Railway

Railway will use `railway.toml` and the Dockerfile. Set the same production env vars as Render. Railway provides `PORT`, so `MCP_PORT` is optional. After deploy, create or use the public Railway domain and use:

```text
https://your-railway-domain.up.railway.app/mcp
```

### Fly.io

Edit `fly.toml` if the app name `poke-mcp` is unavailable, then set secrets and deploy:

```powershell
fly secrets set SUPABASE_URL="<project url>" SUPABASE_SERVICE_ROLE_KEY="<server-side secret>" DANIEL_USER_ID="<Daniel's auth.users id>"
fly deploy
```

`fly.toml` sets `MCP_PORT=8080` and maps Fly's public HTTPS service to internal port `8080`. Health check path: `/health`.

## Deployed Smoke-Test Checklist

After a deployment finishes:

1. Confirm logs show the server starting on `0.0.0.0` and the expected port.
2. Open `https://your-public-host.example.com/health`.
3. Confirm the health payload has `status: "ok"`, `supabase_configured: true`, and no secret values.
4. Run a read-only remote MCP smoke test:

```powershell
.\.venv\Scripts\python scripts\smoke_test.py --url https://your-public-host.example.com/mcp
```

If the remote MCP endpoint requires bearer auth, pass the key through FastMCP's HTTP auth path:

```powershell
.\.venv\Scripts\python scripts\smoke_test.py --url https://your-public-host.example.com/mcp --api-key "<secret>"
```

5. Confirm the smoke test lists tools and returns today's habit dashboard.
6. Connect Poke to `https://your-public-host.example.com/mcp`.
7. From Poke, ask "What habits do I have left today?"
8. Only after read-only checks pass, intentionally test writes with a low-risk habit:

```powershell
.\.venv\Scripts\python scripts\smoke_test.py --url https://your-public-host.example.com/mcp --api-key "<secret>" --write --habit "Creatine"
```

## Connect From Poke

MCP URL:

```text
https://your-public-host.example.com/mcp
```

Auth behavior in this MVP:

- No API-key request header is enforced by the app yet.
- `scripts/smoke_test.py --api-key` sends `Authorization: Bearer <secret>` using FastMCP's HTTP `auth=` support.
- If the host/proxy enforces bearer auth, configure that at the deployment layer and store the value outside git.
- `health()` reports whether `POKE_MCP_API_KEY` is configured, but it does not reveal the key.

Example Poke prompts:

- "What habits do I have left today?"
- "Show my habit dashboard."
- "Mark Creatine complete."
- "Mark Cardio incomplete for today."
- "Did I finish all my habits?"

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
