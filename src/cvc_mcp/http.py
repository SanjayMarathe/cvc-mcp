"""ASGI deployment for the CVC MCP server and its web documentation."""

from __future__ import annotations

import html
import json
import os

from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from cvc_mcp import __version__
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


def _documentation_html(mcp_url: str) -> str:
    safe_mcp_url = html.escape(mcp_url)
    claude_config = json.dumps(
        {"mcpServers": {"cvc": {"url": mcp_url}}}, indent=2, ensure_ascii=False
    )
    safe_config = html.escape(claude_config)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Documentation for the California Virtual Campus MCP server: search CVC online courses and California community college sections from AI assistants.">
  <title>California Virtual Campus MCP Server — Documentation</title>
  <style>
    :root {{ color-scheme: dark; --bg: #07111f; --card: #0d1b2d; --line: #243852;
      --text: #edf5ff; --muted: #a8bdd6; --accent: #65d6ad; --link: #77bdfb; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: radial-gradient(circle at top, #123052 0, var(--bg) 38%);
      color: var(--text); font: 16px/1.6 ui-sans-serif, system-ui, sans-serif; }}
    main {{ width: min(920px, calc(100% - 32px)); margin: 0 auto; padding: 72px 0 96px; }}
    .eyebrow {{ color: var(--accent); font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }}
    h1 {{ max-width: 780px; margin: 10px 0 18px; font-size: clamp(2.4rem, 7vw, 5rem);
      line-height: 1.02; letter-spacing: -.055em; }}
    h2 {{ margin-top: 48px; font-size: 1.55rem; }}
    .lede {{ max-width: 740px; color: var(--muted); font-size: 1.2rem; }}
    .status {{ display: inline-flex; gap: 9px; align-items: center; margin-top: 18px; padding: 7px 12px;
      border: 1px solid #276750; border-radius: 999px; background: #0b2a22; color: #a9f2d7; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 12px var(--accent); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 14px; }}
    .card {{ padding: 20px; border: 1px solid var(--line); border-radius: 14px; background: color-mix(in srgb, var(--card) 92%, transparent); }}
    .card h3 {{ margin: 0 0 6px; font-size: 1rem; color: var(--accent); }}
    .card p {{ margin: 0; color: var(--muted); }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    pre {{ overflow-x: auto; padding: 18px; border: 1px solid var(--line); border-radius: 12px;
      background: #050c16; color: #d9eaff; }}
    a {{ color: var(--link); }}
    .endpoint {{ font-size: 1.05rem; word-break: break-all; }}
    footer {{ margin-top: 56px; padding-top: 22px; border-top: 1px solid var(--line); color: var(--muted); }}
  </style>
</head>
<body>
<main>
  <div class="eyebrow">Model Context Protocol · v{__version__}</div>
  <h1>California Virtual Campus course search for AI assistants.</h1>
  <p class="lede">Search public CVC online courses, retrieve California community college
  class details, and inspect sections, seats, instructors, meeting times, tuition, and
  zero-textbook-cost status through a remote MCP server.</p>
  <div class="status"><span class="dot"></span>Service online · no API key required</div>

  <h2>Connect</h2>
  <p>Use this Streamable HTTP endpoint in Claude, Cursor, Codex, or another MCP client:</p>
  <pre class="endpoint"><code>{safe_mcp_url}</code></pre>
  <p>Generic MCP configuration:</p>
  <pre><code>{safe_config}</code></pre>

  <h2>Tools</h2>
  <div class="grid">
    <section class="card"><h3>search_course_ids</h3><p>Search a college by C-ID, local course symbol, or title.</p></section>
    <section class="card"><h3>get_course</h3><p>Retrieve course metadata and currently displayed sections by CVC ID.</p></section>
    <section class="card"><h3>scrape_course_ids</h3><p>Experimental browser-backed search for local installations with Chrome.</p></section>
    <section class="card"><h3>scrape_courses</h3><p>Experimental browser search plus full course details. Not available on Vercel.</p></section>
  </div>

  <h2>Example prompts</h2>
  <ul>
    <li>“Search CVC for COMP 122 courses at Pasadena City College.”</li>
    <li>“Get the current sections and available seats for CVC course 1052228.”</li>
    <li>“Which listed sections are asynchronous or zero-textbook-cost?”</li>
  </ul>

  <h2>Important</h2>
  <p>This independent project is not affiliated with California Virtual Campus. Course
  availability changes quickly; verify enrollment information on the returned CVC source URL.
  The hosted service is public and read-only.</p>

  <footer><a href="/health">Health check</a> ·
    <a href="https://github.com/SanjayMarathe/cvc-mcp">Source and complete README</a> ·
    Data from <a href="https://search.cvc.edu/">CVC Course Search</a></footer>
</main>
</body>
</html>"""


@mcp.custom_route("/", methods=["GET"])
async def documentation(request: Request) -> HTMLResponse:
    mcp_url = f"{str(request.base_url).rstrip('/')}/mcp"
    return HTMLResponse(_documentation_html(mcp_url))


@mcp.custom_route("/docs", methods=["GET"])
async def docs_redirect(_request: Request) -> RedirectResponse:
    return RedirectResponse("/", status_code=307)


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "service": "cvc-mcp",
            "version": __version__,
            "mcp_endpoint": "/mcp",
        }
    )


app = mcp.streamable_http_app(
    stateless_http=True,
    json_response=True,
    transport_security=_transport_security(),
    host="0.0.0.0",
)
