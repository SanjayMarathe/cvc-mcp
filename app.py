"""Single Vercel ASGI entry point for docs, health, and MCP."""

from cvc_mcp.http import app

__all__ = ["app"]
