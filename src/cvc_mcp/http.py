"""ASGI deployment factory for the CVC MCP server."""

from __future__ import annotations

import os
from importlib.resources import files

from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

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


@mcp.custom_route("/", methods=["GET"])
async def documentation(_request: Request) -> HTMLResponse:
    content = files("cvc_mcp").joinpath("index.html").read_text(encoding="utf-8")
    return HTMLResponse(content)


@mcp.custom_route("/docs", methods=["GET"])
async def docs_redirect(_request: Request) -> RedirectResponse:
    return RedirectResponse("/", status_code=307)


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "service": "cvc-mcp",
            "version": mcp.version,
            "mcp_endpoint": "/mcp",
        }
    )


app = mcp.streamable_http_app(
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
    transport_security=_transport_security(),
    host="0.0.0.0",
)
