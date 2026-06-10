from starlette.testclient import TestClient

from poke_mcp.config import Settings
from poke_mcp.server import create_mcp


def test_http_health_route_is_secret_safe() -> None:
    settings = Settings(
        app_env="test",
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="super-secret",
        daniel_user_id="user-1",
        _env_file=None,
    )
    mcp = create_mcp(settings=settings)

    with TestClient(mcp.http_app(path="/custom-mcp", transport="http")) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["supabase_configured"] is True
    assert "super-secret" not in repr(payload)
