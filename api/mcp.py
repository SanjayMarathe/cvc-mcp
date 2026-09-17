"""Vercel ASGI entry point for Streamable HTTP MCP."""

from cvc_mcp.http import create_app

app = create_app("/api/mcp")
