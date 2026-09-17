"""Opt-in tests against the production Vercel deployment."""

from __future__ import annotations

import json
import os
from urllib.request import urlopen

import pytest
from mcp import Client

BASE_URL = os.getenv("CVC_MCP_E2E_URL", "https://cvc-mcp.vercel.app").rstrip("/")
pytestmark = pytest.mark.skipif(
    os.getenv("CVC_MCP_RUN_E2E") != "1",
    reason="Set CVC_MCP_RUN_E2E=1 to test the live deployment",
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_documentation_and_health() -> None:
    with urlopen(f"{BASE_URL}/", timeout=20) as response:  # noqa: S310
        page = response.read().decode()
    assert "California Virtual Campus MCP Server" in page
    assert "Service online" in page

    with urlopen(f"{BASE_URL}/health", timeout=20) as response:  # noqa: S310
        health = json.load(response)
    assert health["status"] == "ok"
    assert health["service"] == "cvc-mcp"


@pytest.mark.anyio
async def test_search_and_section_seat_counts() -> None:
    async with Client(f"{BASE_URL}/mcp") as client:
        tools = await client.list_tools()
        assert {tool.name for tool in tools.tools} >= {"search_course_ids", "get_course"}

        search = await client.call_tool(
            "search_course_ids",
            {
                "college_name": "Pasadena City College",
                "course_symbol": "COMP 122",
                "max_results": 3,
            },
        )
        course_ids = search.structured_content["course_ids"]
        assert course_ids

        course = await client.call_tool("get_course", {"course_id": int(course_ids[0])})
        sections = course.structured_content["sections"]
        assert sections
        assert all("available_seats" in section for section in sections)
        assert all(isinstance(section["available_seats"], int) for section in sections)
