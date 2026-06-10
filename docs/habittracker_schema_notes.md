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

## Missing Schema

No HabitTracker tables were found for:

- tasks
- daily check-ins
- bodyweight
- sleep
- readiness
- health logs

Task and check-in MCP tools should remain graceful blocked responses until HabitTracker owns those schemas.

## MVP Decision

The `/poke` MVP is safe to implement for HabitTracker habits only. It should not create task/check-in migrations and should not write unrelated data into existing tables.

