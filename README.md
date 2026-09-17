# California Virtual Campus (CVC) MCP Server

[![Model Context Protocol](https://img.shields.io/badge/MCP-compatible-5C4EE5)](https://modelcontextprotocol.io/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An open-source **Model Context Protocol (MCP) server for California Virtual Campus
(CVC)** course search. It lets Claude Desktop and other MCP clients find online classes
at California community colleges and retrieve course details, prerequisites, sections,
available seats, instructors, tuition, meeting times, and zero-textbook-cost status.

This server wraps the unofficial
[`CaliforniaVirtualCampusAPI`](https://github.com/rob-m1/california-virtual-campus-api)
Python library and public data from [CVC Course Search](https://search.cvc.edu/).
**No API key is required.**

## Features

- Search California Virtual Campus course IDs by college, C-ID, local course code, or title
- Retrieve structured CVC course and section data for AI assistants
- Find online California community college classes from Claude Desktop
- Return source URLs so users can verify current information on CVC
- Limit results to protect the model context window
- Offer optional Selenium browser-search fallbacks for difficult queries
- Run locally over stdio; no hosted service, account, or API key required
- Deploy as a stateless Streamable HTTP MCP server on Vercel

## MCP tools

| Tool | Description |
|---|---|
| `search_course_ids` | Search one college by C-ID, course symbol, or course name using CVC's public search endpoint |
| `get_course` | Get detailed course information and currently displayed sections by CVC course ID |
| `scrape_course_ids` | Experimental headless-browser course search |
| `scrape_courses` | Experimental headless-browser search with full course details |

For reliable results, call `search_course_ids` first and pass an ID to `get_course`.
The two `scrape_*` tools require a local Chrome or Chromium installation and a compatible
ChromeDriver. They are slower and more sensitive to CVC website changes.

## Requirements

- Python 3.10 or newer
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`
- Internet access to `search.cvc.edu`
- Chrome/Chromium only when using the experimental `scrape_*` tools

## Install

```bash
git clone https://github.com/SanjayMarathe/cvc-mcp.git
cd cvc-mcp
uv sync --frozen
```

Run the server locally:

```bash
uv run --frozen cvc-mcp
```

The process waits for MCP messages on standard input; a blank terminal is expected.

### Install with pip

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install .
cvc-mcp
```

## Add CVC MCP to Claude Desktop

Open the Claude Desktop configuration file:

| Operating system | Configuration path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\\Claude\\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

Add this entry under `mcpServers`, replacing both paths with absolute paths on your
computer:

```json
{
  "mcpServers": {
    "cvc": {
      "command": "/absolute/path/to/uv",
      "args": [
        "--directory",
        "/absolute/path/to/cvc-mcp",
        "run",
        "--frozen",
        "cvc-mcp"
      ]
    }
  }
}
```

Fully quit and reopen Claude Desktop. Ask Claude to list its tools if the CVC tools do
not appear immediately.

## Hosted MCP and documentation

This repository includes a Vercel-compatible Python ASGI deployment:

- `/` — browsable setup and tool documentation
- `/docs` — redirects to the documentation homepage
- `/health` — JSON health check
- `/mcp` — stateless Streamable HTTP MCP endpoint

Deploy your own copy with the Vercel CLI:

```bash
vercel
vercel --prod
```

Vercel supplies the deployment hostname automatically. The server uses it to enforce
MCP host and origin checks. If you deploy through another ASGI platform, set
`CVC_MCP_HOST` to its hostname without `https://`.

Connect a remote MCP client with:

```json
{
  "mcpServers": {
    "cvc": {
      "url": "https://your-project.vercel.app/mcp"
    }
  }
}
```

The hosted MCP endpoint is public and read-only. No API key is required. The
`scrape_*` tools require Chrome and therefore are intended for local use; use
`search_course_ids` and `get_course` on Vercel.

## Example prompts for Claude

- “Search CVC for online computer science courses at Pasadena City College.”
- “Find the CVC course IDs for COMP 122 and show me the available sections.”
- “Does this California community college course have open seats or zero textbook cost?”
- “Compare the instructors, meeting times, and tuition for these CVC course IDs.”
- “Find an online California community college class that matches C-ID COMP 122.”

## Tool examples

Search for matching IDs:

```json
{
  "college_name": "Pasadena City College",
  "course_symbol": "COMP 122",
  "max_results": 10
}
```

Retrieve course details:

```json
{
  "course_id": 12345
}
```

## How it works

The server uses the official Python SDK for the Model Context Protocol and delegates CVC
lookups to `CaliforniaVirtualCampusAPI` 0.0.2. The upstream library reads public CVC web
pages and a public search endpoint, then this MCP server converts its Python course and
section objects into stable, model-friendly JSON.

All requests run locally from your computer. There is no API key, analytics service, or
intermediate hosted backend in this project.

## Limitations and data accuracy

- This is an independent, unofficial project. It is not affiliated with or endorsed by
  California Virtual Campus, the California Community Colleges Chancellor's Office, or
  Anthropic.
- The upstream wrapper is alpha software and depends on CVC's current HTML structure.
- Course availability, seat counts, tuition, dates, transferability, and prerequisites
  can change. Always verify results on the returned `search.cvc.edu` source URL and with
  the teaching college before enrolling.
- College-name matching is performed by the upstream package and may select a similarly
  named institution when given an ambiguous or misspelled name.
- CVC can change or restrict its public endpoints at any time.

## Development

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Run the HTTP deployment locally:

```bash
uv run uvicorn cvc_mcp.http:app --reload
# Documentation: http://127.0.0.1:8000/
# MCP endpoint:  http://127.0.0.1:8000/mcp
```

## Data source and attribution

Course data is provided by [California Virtual Campus](https://www.cvc.edu/) and is
described by the upstream project as available under the Creative Commons Attribution
4.0 International license. The wrapper dependency is licensed under Apache-2.0. This
MCP server's original code is available under the [MIT License](LICENSE).

## Related terms

California Virtual Campus API, CVC API, CVC Exchange, CVC Course Finder, California
community college online courses, California online classes, Claude Desktop MCP server,
Model Context Protocol course search, community college course availability.
