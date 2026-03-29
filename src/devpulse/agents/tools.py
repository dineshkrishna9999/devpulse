"""Tool functions for the DevPulse agent.

Each function here is a "tool" the ADK agent can call.
They fetch real data from external APIs and return JSON strings.

Why JSON strings? ADK tools must return strings — the agent reads the JSON,
understands the data, and uses it to build its response.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

# Shared HTTP timeout for all API calls (seconds).
_TIMEOUT = 10


def fetch_pypi_releases(package_name: str) -> str:
    """Fetch the latest release info for a PyPI package.

    Args:
        package_name: Name of the package on PyPI (e.g. "litellm", "google-adk").

    Returns:
        JSON string with version, summary, and recent versions.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        resp = httpx.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        info = data["info"]
        recent_versions = sorted(data["releases"].keys(), reverse=True)[:5]

        return json.dumps(
            {
                "package": package_name,
                "latest_version": info["version"],
                "summary": info["summary"],
                "home_page": info.get("home_page") or info.get("project_url", ""),
                "project_urls": info.get("project_urls", {}),
                "requires_python": info.get("requires_python", ""),
                "recent_versions": recent_versions,
            }
        )
    except Exception as exc:
        logger.warning("PyPI fetch failed for %s: %s", package_name, exc)
        return json.dumps({"error": f"Failed to fetch {package_name}: {exc}"})


def fetch_github_trending(language: str = "python", since: str = "weekly") -> str:
    """Fetch trending repositories from GitHub.

    Uses the GitHub search API to find recently created repos with high star
    counts — a good proxy for "trending" since GitHub has no official trending API.

    Args:
        language: Programming language to filter by (e.g. "python", "javascript").
        since: Time range — "daily", "weekly", or "monthly".

    Returns:
        JSON string with a list of trending repos (name, description, stars, url).
    """
    today = datetime.now()

    if since == "daily":
        date_str = today.strftime("%Y-%m-%d")
    elif since == "monthly":
        date_str = f"{today.year}-{today.month:02d}-01"
    else:
        week_ago = today - timedelta(days=7)
        date_str = week_ago.strftime("%Y-%m-%d")

    params: dict[str, str | int] = {
        "q": f"language:{language} created:>{date_str}",
        "sort": "stars",
        "order": "desc",
        "per_page": 10,
    }
    try:
        resp = httpx.get("https://api.github.com/search/repositories", params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        repos = [
            {
                "name": repo["full_name"],
                "description": repo.get("description", ""),
                "stars": repo["stargazers_count"],
                "url": repo["html_url"],
                "language": repo.get("language", ""),
            }
            for repo in data.get("items", [])[:10]
        ]
        return json.dumps({"trending": repos, "language": language, "since": since})
    except Exception as exc:
        logger.warning("GitHub trending fetch failed: %s", exc)
        return json.dumps({"error": f"Failed to fetch trending: {exc}"})


def fetch_hackernews_top(query: str = "AI", limit: int = 10) -> str:
    """Fetch top Hacker News stories matching a query.

    Uses the HN Algolia search API — fast and doesn't need authentication.

    Args:
        query: Search term to filter stories (e.g. "AI", "python", "LLM").
        limit: Maximum number of stories to return (default 10).

    Returns:
        JSON string with a list of stories (title, url, points, comments).
    """
    params: dict[str, str | int] = {
        "query": query,
        "tags": "story",
        "hitsPerPage": limit,
    }
    try:
        resp = httpx.get("https://hn.algolia.com/api/v1/search", params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        stories = [
            {
                "title": hit["title"],
                "url": hit.get("url", f"https://news.ycombinator.com/item?id={hit['objectID']}"),
                "points": hit.get("points", 0),
                "comments": hit.get("num_comments", 0),
            }
            for hit in data.get("hits", [])
        ]
        return json.dumps({"stories": stories, "query": query})
    except Exception as exc:
        logger.warning("HN fetch failed for query '%s': %s", query, exc)
        return json.dumps({"error": f"Failed to fetch HN: {exc}"})
