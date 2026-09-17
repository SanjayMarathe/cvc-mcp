"""MCP tools for public California Virtual Campus course data."""

from __future__ import annotations

from functools import partial
from typing import Any

import anyio
import cvc
from mcp.server import MCPServer

from cvc_mcp import __version__

SERVER_NAME = "California Virtual Campus Course Search"
MAX_RESULTS_LIMIT = 100

mcp = MCPServer(
    SERVER_NAME,
    title="California Virtual Campus MCP Server",
    description="Search public CVC online courses and California community college sections.",
    instructions=(
        "Search public California Virtual Campus (CVC) online course listings. "
        "Start with search_course_ids, then call get_course for detailed course and "
        "section data. Prefer the non-browser tools unless browser scraping is necessary."
    ),
    website_url="https://github.com/SanjayMarathe/cvc-mcp",
    version=__version__,
)


def _validate_max_results(max_results: int) -> None:
    if not 1 <= max_results <= MAX_RESULTS_LIMIT:
        raise ValueError(f"max_results must be between 1 and {MAX_RESULTS_LIMIT}")


def _seat_count(value: Any) -> int | str:
    """Normalize the numeric seat counts returned as strings by the upstream scraper."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip().replace(",", ""))
    except ValueError:
        return str(value).strip()


def _section_to_dict(section: Any) -> dict[str, Any]:
    return {
        "semester": getattr(section, "semester", ""),
        "duration": getattr(section, "duration", ""),
        "section": getattr(section, "section", ""),
        "format": getattr(section, "format", ""),
        "zero_textbook_cost": bool(getattr(section, "zeroTextbookCost", False)),
        "meeting_times": list(getattr(section, "time", []) or []),
        "professor": getattr(section, "prof", ""),
        "available_seats": _seat_count(getattr(section, "currSeatCount", 0)),
        "tuition": getattr(section, "tuition", 0),
        "registration": getattr(section, "registration", ""),
        "section_note": getattr(section, "sectionNote", ""),
    }


def _course_to_dict(course: Any) -> dict[str, Any]:
    return {
        "cvc_id": str(getattr(course, "cvc_id", "")),
        "college_name": getattr(course, "college_name", ""),
        "course_name": getattr(course, "class_name", ""),
        "course_symbol": getattr(course, "class_symbol", ""),
        "c_id": getattr(course, "C_ID", ""),
        "description": getattr(course, "course_description", ""),
        "location": getattr(course, "location", ""),
        "units": getattr(course, "units", 0),
        "unit_type": getattr(course, "unitType", ""),
        "prerequisites": list(getattr(course, "prereqs", []) or []),
        "sections": [
            _section_to_dict(section) for section in (getattr(course, "sections", []) or [])
        ],
        "source_url": f"https://search.cvc.edu/courses/{getattr(course, 'cvc_id', '')}",
    }


async def _run_upstream(function: Any, *args: Any, timeout_seconds: float = 30) -> Any:
    """Run the synchronous upstream scraper without blocking the MCP event loop."""
    try:
        with anyio.fail_after(timeout_seconds):
            return await anyio.to_thread.run_sync(partial(function, *args), abandon_on_cancel=True)
    except TimeoutError as exc:
        raise RuntimeError(f"CVC request timed out after {timeout_seconds:g} seconds") from exc
    except Exception as exc:
        raise RuntimeError(f"CVC request failed: {exc}") from exc


async def _search_ids(
    college_name: str,
    c_id: str,
    course_symbol: str,
    course_name: str,
    max_results: int,
    *,
    browser: bool,
) -> dict[str, Any]:
    _validate_max_results(max_results)
    if not college_name.strip():
        raise ValueError("college_name is required")
    if not any(value.strip() for value in (c_id, course_symbol, course_name)):
        raise ValueError("Provide at least one of c_id, course_symbol, or course_name")

    function = cvc.getCourseIDsByScraping if browser else cvc.getCourseIDsBySearch
    ids = await _run_upstream(
        function,
        college_name.strip(),
        c_id.strip(),
        course_symbol.strip(),
        course_name.strip(),
        timeout_seconds=45 if browser else 20,
    )
    normalized = [str(course_id) for course_id in ids]
    return {
        "course_ids": normalized[:max_results],
        "returned": min(len(normalized), max_results),
        "total_found": len(normalized),
        "truncated": len(normalized) > max_results,
        "search_method": "browser_scraping" if browser else "cvc_search_api",
    }


@mcp.tool()
async def search_course_ids(
    college_name: str,
    c_id: str = "",
    course_symbol: str = "",
    course_name: str = "",
    max_results: int = 25,
) -> dict[str, Any]:
    """Search CVC course IDs at a California community college.

    Use a college name plus at least one filter. C-ID is the statewide Course
    Identification Numbering System value; course_symbol is the local code such as
    COMPSCI001; course_name is a title phrase. This is the preferred, lightweight search.
    """
    return await _search_ids(
        college_name, c_id, course_symbol, course_name, max_results, browser=False
    )


@mcp.tool()
async def get_course(course_id: int) -> dict[str, Any]:
    """Get a CVC course and its sections, including available seats for each section."""
    if course_id <= 0:
        raise ValueError("course_id must be a positive integer")
    course = await _run_upstream(cvc.getCourseContentByID, course_id)
    return _course_to_dict(course)


@mcp.tool()
async def scrape_course_ids(
    college_name: str,
    c_id: str = "",
    course_symbol: str = "",
    course_name: str = "",
    max_results: int = 25,
) -> dict[str, Any]:
    """Search CVC course IDs through a headless Chrome browser.

    This experimental fallback is slower and requires Chrome/Chromium plus a compatible
    driver. Prefer search_course_ids for ordinary searches.
    """
    return await _search_ids(
        college_name, c_id, course_symbol, course_name, max_results, browser=True
    )


@mcp.tool()
async def scrape_courses(
    college_name: str,
    c_id: str = "",
    course_symbol: str = "",
    course_name: str = "",
    max_results: int = 10,
) -> dict[str, Any]:
    """Search CVC in a headless browser and return detailed matching courses.

    This experimental operation can be slow because it loads a page for every result.
    It requires Chrome/Chromium and a compatible driver. Prefer search_course_ids followed
    by get_course when possible.
    """
    result = await _search_ids(
        college_name, c_id, course_symbol, course_name, max_results, browser=True
    )
    courses = []
    for course_id in result["course_ids"]:
        course = await _run_upstream(cvc.getCourseContentByID, int(course_id))
        courses.append(_course_to_dict(course))
    return {
        "courses": courses,
        "returned": len(courses),
        "total_found": result["total_found"],
        "truncated": result["truncated"],
        "search_method": "browser_scraping",
    }


def main() -> None:
    """Run the MCP server over stdio for Claude Desktop and other local clients."""
    mcp.run()


if __name__ == "__main__":
    main()
