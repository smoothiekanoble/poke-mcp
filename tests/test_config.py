from poke_mcp.config import Settings


def test_config_defaults(monkeypatch) -> None:
    for key in [
        "APP_ENV",
        "APP_TIMEZONE",
        "MCP_HOST",
        "MCP_PORT",
        "MCP_PATH",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "DANIEL_USER_ID",
        "POKE_MCP_API_KEY",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.app_timezone == "America/Chicago"
    assert settings.mcp_host == "127.0.0.1"
    assert settings.mcp_port == 8000
    assert settings.mcp_path == "/mcp"
    assert settings.supabase_configured is False
    assert settings.google_calendar_configured is False


def test_config_detects_supabase(monkeypatch) -> None:
    for key in [
        "APP_ENV",
        "APP_TIMEZONE",
        "MCP_HOST",
        "MCP_PORT",
        "MCP_PATH",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "DANIEL_USER_ID",
        "POKE_MCP_API_KEY",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="secret-service-role",
        daniel_user_id="user-1",
        _env_file=None,
    )

    assert settings.supabase_configured is True


def test_config_accepts_platform_port(monkeypatch) -> None:
    monkeypatch.delenv("MCP_PORT", raising=False)
    monkeypatch.setenv("PORT", "9001")

    settings = Settings(_env_file=None)

    assert settings.mcp_port == 9001
