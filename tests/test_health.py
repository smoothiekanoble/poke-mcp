from poke_mcp.config import Settings
from poke_mcp.tools.health_tools import build_health_payload


def test_health_is_secret_safe() -> None:
    settings = Settings(
        app_env="test",
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="super-secret-service-role",
        daniel_user_id="user-1",
        poke_mcp_api_key="super-secret-api-key",
        _env_file=None,
    )

    payload = build_health_payload(settings)
    payload_text = repr(payload)

    assert payload["status"] == "ok"
    assert payload["supabase_configured"] is True
    assert payload["api_key_configured"] is True
    assert "super-secret-service-role" not in payload_text
    assert "super-secret-api-key" not in payload_text

