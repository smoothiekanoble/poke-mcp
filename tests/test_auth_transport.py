import pytest
from fastmcp import Client
from fastmcp.utilities.tests import run_server_async

from poke_mcp.config import Settings
from poke_mcp.server import create_mcp


async def test_remote_http_client_auth_matches_server_api_key() -> None:
    settings = Settings(poke_mcp_api_key="expected-secret", _env_file=None)
    mcp = create_mcp(settings=settings)

    async with run_server_async(mcp, path="/mcp") as url:
        async with Client(url, auth="expected-secret") as client:
            tools = await client.list_tools()

    assert "health" in {tool.name for tool in tools}


async def test_remote_http_client_rejects_missing_or_wrong_api_key() -> None:
    settings = Settings(poke_mcp_api_key="expected-secret", _env_file=None)
    mcp = create_mcp(settings=settings)

    async with run_server_async(mcp, path="/mcp") as url:
        with pytest.raises(Exception, match="Unauthorized|Session terminated|401"):
            async with Client(url) as client:
                await client.list_tools()

        with pytest.raises(Exception, match="Unauthorized|Session terminated|401"):
            async with Client(url, auth="wrong-secret") as client:
                await client.list_tools()
