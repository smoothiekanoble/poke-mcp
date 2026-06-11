# HabitTracker Schema Notes

Inspected adjacent repo: `C:\dev\personal\habittracker`

## Tables Found

### `public.habits`

Columns used by `/poke`:

- `id`
- `user_id`
- `title`
- `active_from`
- `active_until`
- `created_at`

Other known columns:

- `color`
- `icon`
- `updated_at`

Migrations found:

- `supabase/migrations/20250101000001_create_habits.sql`
- `supabase/migrations/20250404120000_habits_active_range.sql`

### `public.habit_logs`

Columns used by `/poke`:

- `habit_id`
- `date`
- `completed`

Other known columns:

- `id`
- `created_at`

Migration found:

- `supabase/migrations/20250101000002_create_habit_logs.sql`

The table has a unique constraint on `(habit_id, date)`, which supports idempotent upserts.

### `public.daily_metrics`

Daily summarized imported metrics (MedM body-weight import). Verified against live
Supabase on 2026-06-10; no migration file exists in the HabitTracker repo.

Columns used by `/poke` (read-only):

- `user_id`
- `metric_date` (date, `YYYY-MM-DD`)
- `metric_type` (e.g. `body_weight`)
- `value` (numeric)
- `unit` (e.g. `lb`)
- `source` (e.g. `medm_health`)

Other known columns: `id`, `source_detail` (jsonb), `created_at`, `updated_at`.

### `public.metric_events`

Event-level imported measurements. Verified against live Supabase on 2026-06-10.

Columns used by `/poke` (read-only):

- `user_id`
- `occurred_at` (timestamptz)
- `metric_date`
- `metric_type`
- `value`
- `unit`
- `source`
- `source_detail` (text, device name)

Other known columns: `id`, `source_record_id`, `raw_metadata` (jsonb), `created_at`,
`updated_at`.

`/poke` metric tools query `daily_metrics` for summaries/history and only touch
`metric_events` for latest raw event details. Both tables are read-only from `/poke`.

## Missing Schema

No HabitTracker tables were found for:

- tasks
- daily check-ins
- sleep
- readiness
- health logs

Task and check-in MCP tools should remain graceful blocked responses until HabitTracker owns those schemas.

## MVP Decision

The `/poke` MVP is safe to implement for HabitTracker habits only. It should not create task/check-in migrations and should not write unrelated data into existing tables.

