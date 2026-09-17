"""ASGI deployment factory for the CVC MCP server."""

from __future__ import annotations

import os

from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette

from cvc_mcp.server import mcp


def _transport_security() -> TransportSecuritySettings:
    hosts = ["127.0.0.1:*", "localhost:*", "testserver"]
    origins = ["http://127.0.0.1:*", "http://localhost:*", "http://testserver"]

    for variable in ("VERCEL_URL", "VERCEL_PROJECT_PRODUCTION_URL", "CVC_MCP_HOST"):
        host = os.getenv(variable, "").strip().removeprefix("https://").removeprefix("http://")
        if host:
            hosts.append(host)
            origins.append(f"https://{host}")

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def create_app(path: str = "/mcp") -> Starlette:
    """Create a stateless ASGI MCP app at the requested public path."""
    return mcp.streamable_http_app(
        streamable_http_path=path,
        stateless_http=True,
        json_response=True,
        transport_security=_transport_security(),
        host="0.0.0.0",
    )
