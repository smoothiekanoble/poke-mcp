"""Small auth helpers for future hosted Poke integration."""

from __future__ import annotations

import hashlib
import hmac
import logging

from fastmcp.server.auth import AccessToken, TokenVerifier

from poke_mcp.config import Settings

logger = logging.getLogger(__name__)


def api_key_configured(settings: Settings) -> bool:
    return bool(settings.poke_mcp_api_key)


def verify_api_key(provided_api_key: str | None, settings: Settings) -> bool:
    """Return true when auth is disabled or the provided API key matches."""
    if not settings.poke_mcp_api_key:
        return True
    if not provided_api_key:
        return False
    return hmac.compare_digest(provided_api_key, settings.poke_mcp_api_key)


def token_fingerprint(token: str | None) -> str:
    if not token:
        return "none"
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]


class PokeApiKeyVerifier(TokenVerifier):
    """FastMCP bearer-token verifier backed by POKE_MCP_API_KEY."""

    def __init__(self, api_key: str) -> None:
        super().__init__()
        self._api_key = api_key
        logger.info(
            "Poke MCP bearer auth verifier initialized expected_key_fingerprint=%s",
            token_fingerprint(api_key),
        )

    async def verify_token(self, token: str) -> AccessToken | None:
        fingerprint = token_fingerprint(token)
        if not hmac.compare_digest(token, self._api_key):
            logger.warning(
                "Poke MCP bearer auth rejected token_fingerprint=%s",
                fingerprint,
            )
            return None

        logger.info(
            "Poke MCP bearer auth accepted token_fingerprint=%s",
            fingerprint,
        )
        return AccessToken(
            token=token,
            client_id="poke-api-key",
            scopes=[],
            claims={"auth_method": "poke_api_key"},
        )
