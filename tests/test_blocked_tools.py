from poke_mcp.tools.blocked_tools import blocked_checkin_response, blocked_task_response


def test_blocked_task_response_names_missing_schema() -> None:
    response = blocked_task_response()

    assert response["status"] == "blocked"
    assert response["missing_schema"] == "tasks"


def test_blocked_checkin_response_names_missing_schema() -> None:
    response = blocked_checkin_response()

    assert response["status"] == "blocked"
    assert response["missing_schema"] == "daily_checkins"

