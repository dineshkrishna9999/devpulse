"""Data models for DevPulse.

All data flowing through the system is represented by these dataclasses.
Sources produce them, agents consume them, and the renderer displays them.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────


class ItemType(StrEnum):
    """Type of item being tracked."""

    PYPI = "pypi"
    GITHUB = "github"
    TOPIC = "topic"


class Priority(StrEnum):
    """Briefing item priority level."""

    CRITICAL = "critical"
    IMPORTANT = "important"
    FYI = "fyi"


class BriefingCategory(StrEnum):
    """Category of a briefing item."""

    RELEASE = "release"
    TRENDING = "trending"
    NEWS = "news"
    CONTENT = "content"


# ──────────────────────────────────────────────
# Tracked Items
# ──────────────────────────────────────────────


@dataclass
class TrackedItem:
    """An item the user wants to track (package, repo, or topic).

    Examples:
        TrackedItem(name="litellm", item_type=ItemType.PYPI, current_version="1.40.0")
        TrackedItem(name="BerriAI/litellm", item_type=ItemType.GITHUB)
        TrackedItem(name="AI agents", item_type=ItemType.TOPIC)
    """

    name: str
    item_type: ItemType
    source_url: str | None = None
    current_version: str | None = None
    added_at: datetime = field(default_factory=datetime.now)
    last_checked: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        data = asdict(self)
        data["item_type"] = self.item_type.value
        data["added_at"] = self.added_at.isoformat()
        data["last_checked"] = self.last_checked.isoformat() if self.last_checked else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrackedItem:
        """Create a TrackedItem from a dict (e.g. loaded from JSON)."""
        return cls(
            name=data["name"],
            item_type=ItemType(data["item_type"]),
            source_url=data.get("source_url"),
            current_version=data.get("current_version"),
            added_at=datetime.fromisoformat(data["added_at"]),
            last_checked=datetime.fromisoformat(data["last_checked"]) if data.get("last_checked") else None,
        )


# ──────────────────────────────────────────────
# Source Data (produced by fetchers)
# ──────────────────────────────────────────────


@dataclass
class ReleaseInfo:
    """A package release fetched from PyPI or GitHub.

    Represents a single version release with its changelog and metadata.
    """

    package: str
    version: str
    published_at: datetime
    summary: str
    breaking: bool = False
    changelog_url: str = ""
    highlights: list[str] = field(default_factory=list)


@dataclass
class TrendingItem:
    """A trending item from GitHub, HN, or Reddit.

    Represents something noteworthy happening in the ecosystem.
    """

    title: str
    source: str  # "github", "hackernews", "reddit"
    url: str
    score: int  # stars, upvotes, points
    description: str = ""
    relevance: str | None = None  # AI-generated: why this matters to the user


# ──────────────────────────────────────────────
# Briefing (produced by agents, consumed by renderer)
# ──────────────────────────────────────────────


@dataclass
class BriefingItem:
    """A single item in a DevPulse briefing.

    Each item has a priority level and optionally an AI-generated insight
    explaining why it matters to the user specifically.
    """

    priority: Priority
    category: BriefingCategory
    title: str
    body: str
    source_url: str = ""
    ai_insight: str | None = None
    relevance_score: float = 0.0  # 0.0 to 1.0

    @property
    def priority_emoji(self) -> str:
        """Get the emoji for this item's priority level."""
        mapping = {
            Priority.CRITICAL: "🔴",
            Priority.IMPORTANT: "🟡",
            Priority.FYI: "🟢",
        }
        return mapping[self.priority]


@dataclass
class Briefing:
    """A complete DevPulse briefing — the final output.

    Contains all briefing items sorted by priority, plus metadata
    about when/how the briefing was generated.
    """

    generated_at: datetime
    tracked_count: int
    items: list[BriefingItem] = field(default_factory=list)
    content_ideas: list[str] | None = None
    model_used: str | None = None

    @property
    def critical_items(self) -> list[BriefingItem]:
        """Get items with critical priority."""
        return [i for i in self.items if i.priority == Priority.CRITICAL]

    @property
    def important_items(self) -> list[BriefingItem]:
        """Get items with important priority."""
        return [i for i in self.items if i.priority == Priority.IMPORTANT]

    @property
    def fyi_items(self) -> list[BriefingItem]:
        """Get items with FYI priority."""
        return [i for i in self.items if i.priority == Priority.FYI]

    def to_json(self) -> str:
        """Serialize the entire briefing to JSON."""
        data = asdict(self)
        data["generated_at"] = self.generated_at.isoformat()
        data["items"] = [
            {
                **asdict(item),
                "priority": item.priority.value,
                "category": item.category.value,
            }
            for item in self.items
        ]
        if self.model_used is None:
            data["model_used"] = None
        return json.dumps(data, indent=2)
