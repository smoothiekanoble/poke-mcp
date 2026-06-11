from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FakeResponse:
    data: list[dict[str, Any]]


class FakeSupabase:
    def __init__(self, tables: dict[str, list[dict[str, Any]]] | None = None) -> None:
        self.tables = tables or {}
        self.operations: list[dict[str, Any]] = []

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self, name)


class FakeQuery:
    def __init__(self, supabase: FakeSupabase, table_name: str) -> None:
        self._supabase = supabase
        self._table_name = table_name
        self._action = "select"
        self._filters: list[tuple[str, str, Any]] = []
        self._payload: dict[str, Any] | None = None
        self._on_conflict: str | None = None
        self._order_by: tuple[str, bool] | None = None
        self._limit: int | None = None

    def select(self, columns: str = "*") -> FakeQuery:
        _ = columns
        self._action = "select"
        return self

    def eq(self, field: str, value: Any) -> FakeQuery:
        self._filters.append(("eq", field, value))
        return self

    def in_(self, field: str, values: list[Any]) -> FakeQuery:
        self._filters.append(("in", field, list(values)))
        return self

    def gte(self, field: str, value: Any) -> FakeQuery:
        self._filters.append(("gte", field, value))
        return self

    def lte(self, field: str, value: Any) -> FakeQuery:
        self._filters.append(("lte", field, value))
        return self

    def order(self, field: str, *, desc: bool = False) -> FakeQuery:
        self._order_by = (field, desc)
        return self

    def limit(self, count: int) -> FakeQuery:
        self._limit = count
        return self

    def upsert(
        self,
        payload: dict[str, Any],
        *,
        on_conflict: str | None = None,
    ) -> FakeQuery:
        self._action = "upsert"
        self._payload = dict(payload)
        self._on_conflict = on_conflict
        return self

    def execute(self) -> FakeResponse:
        if self._action == "upsert":
            return self._execute_upsert()
        return self._execute_select()

    def _execute_select(self) -> FakeResponse:
        rows = [dict(row) for row in self._supabase.tables.get(self._table_name, [])]
        for kind, field, value in self._filters:
            if kind == "eq":
                rows = [row for row in rows if row.get(field) == value]
            elif kind == "in":
                allowed = {str(item) for item in value}
                rows = [row for row in rows if str(row.get(field)) in allowed]
            elif kind == "gte":
                rows = [row for row in rows if str(row.get(field) or "") >= str(value)]
            elif kind == "lte":
                rows = [row for row in rows if str(row.get(field) or "") <= str(value)]
        if self._order_by:
            field, desc = self._order_by
            rows.sort(key=lambda row: str(row.get(field) or ""), reverse=desc)
        if self._limit is not None:
            rows = rows[: self._limit]
        self._supabase.operations.append(
            {
                "action": "select",
                "table": self._table_name,
                "filters": list(self._filters),
            }
        )
        return FakeResponse(rows)

    def _execute_upsert(self) -> FakeResponse:
        if self._payload is None:
            raise AssertionError("upsert called without payload")
        rows = self._supabase.tables.setdefault(self._table_name, [])
        if self._table_name == "habit_logs" and self._on_conflict == "habit_id,date":
            for row in rows:
                if (
                    row.get("habit_id") == self._payload["habit_id"]
                    and row.get("date") == self._payload["date"]
                ):
                    row.update(self._payload)
                    payload = dict(row)
                    break
            else:
                payload = {
                    "id": f"fake-log-{len(rows) + 1}",
                    "created_at": "2026-06-09T00:00:00Z",
                    **self._payload,
                }
                rows.append(payload)
        else:
            payload = dict(self._payload)
            rows.append(payload)

        self._supabase.operations.append(
            {
                "action": "upsert",
                "table": self._table_name,
                "payload": dict(self._payload),
                "on_conflict": self._on_conflict,
            }
        )
        return FakeResponse([payload])

