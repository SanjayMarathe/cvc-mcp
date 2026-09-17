from __future__ import annotations

from types import SimpleNamespace

import pytest
from mcp import Client

from cvc_mcp import server


@pytest.mark.anyio
async def test_mcp_exposes_expected_tools() -> None:
    async with Client(server.mcp) as client:
        result = await client.list_tools()

    assert {tool.name for tool in result.tools} == {
        "get_course",
        "scrape_course_ids",
        "scrape_courses",
        "search_course_ids",
    }


def test_course_serialization() -> None:
    section = SimpleNamespace(
        semester="Fall 2026",
        duration="Aug 24-Dec 18",
        section="12345",
        format="Online asynchronous",
        zeroTextbookCost=True,
        time=["TBA"],
        prof="Ada Lovelace",
        currSeatCount="12",
        tuition="$0",
        registration="Open",
        sectionNote="",
    )
    course = SimpleNamespace(
        cvc_id=42,
        college_name="Example College",
        class_name="Introduction to Computing",
        class_symbol="CIS 101",
        C_ID="COMP 100",
        course_description="An introductory course.",
        location="Online",
        units="3.0",
        unitType="Semester",
        prereqs=["MATH 100"],
        sections=[section],
    )

    result = server._course_to_dict(course)

    assert result["cvc_id"] == "42"
    assert result["sections"][0]["zero_textbook_cost"] is True
    assert result["source_url"] == "https://search.cvc.edu/courses/42"


@pytest.mark.anyio
async def test_search_ids_limits_results(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cvc := server.cvc, "getCourseIDsBySearch", lambda *_: [1, 2, 3])

    result = await server._search_ids("Pasadena City College", "", "COMP", "", 2, browser=False)

    assert cvc is server.cvc
    assert result == {
        "course_ids": ["1", "2"],
        "returned": 2,
        "total_found": 3,
        "truncated": True,
        "search_method": "cvc_search_api",
    }


@pytest.mark.anyio
async def test_search_requires_a_filter() -> None:
    with pytest.raises(ValueError, match="at least one"):
        await server._search_ids("Pasadena City College", "", "", "", 10, browser=False)


@pytest.mark.parametrize("value", [0, 101])
def test_result_limit_validation(value: int) -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        server._validate_max_results(value)
