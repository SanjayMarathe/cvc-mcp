"""Vercel health-check function."""

import json
from http.server import BaseHTTPRequestHandler

from cvc_mcp import __version__


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = json.dumps(
            {
                "status": "ok",
                "service": "cvc-mcp",
                "version": __version__,
                "mcp_endpoint": "/mcp",
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
