"""Tests for devpulse data models."""

import json
from datetime import datetime

from devpulse.models import (
    Briefing,
    BriefingCategory,
    BriefingItem,
    ItemType,
    Priority,
    ReleaseInfo,
    TrackedItem,
    TrendingItem,
)


class TestTrackedItem:
    """Tests for TrackedItem dataclass."""

    def test_create_pypi_item(self) -> None:
        item = TrackedItem(name="litellm", item_type=ItemType.PYPI, current_version="1.40.0")
        assert item.name == "litellm"
        assert item.item_type == ItemType.PYPI
        assert item.current_version == "1.40.0"
        assert item.source_url is None
        assert item.last_checked is None

    def test_create_github_item(self) -> None:
        item = TrackedItem(
            name="BerriAI/litellm",
            item_type=ItemType.GITHUB,
            source_url="https://github.com/BerriAI/litellm",
        )
        assert item.item_type == ItemType.GITHUB
        assert item.source_url == "https://github.com/BerriAI/litellm"

    def test_create_topic_item(self) -> None:
        item = TrackedItem(name="AI agents", item_type=ItemType.TOPIC)
        assert item.item_type == ItemType.TOPIC

    def test_to_dict(self) -> None:
        now = datetime(2026, 3, 29, 12, 0, 0)
        item = TrackedItem(
            name="litellm",
            item_type=ItemType.PYPI,
            current_version="1.40.0",
            added_at=now,
        )
        data = item.to_dict()
        assert data["name"] == "litellm"
        assert data["item_type"] == "pypi"
        assert data["added_at"] == "2026-03-29T12:00:00"
        assert data["last_checked"] is None

    def test_from_dict_roundtrip(self) -> None:
        now = datetime(2026, 3, 29, 12, 0, 0)
        original = TrackedItem(
            name="litellm",
            item_type=ItemType.PYPI,
            current_version="1.40.0",
            added_at=now,
        )
        data = original.to_dict()
        restored = TrackedItem.from_dict(data)
        assert restored.name == original.name
        assert restored.item_type == original.item_type
        assert restored.current_version == original.current_version
        assert restored.added_at == original.added_at

    def test_from_dict_with_last_checked(self) -> None:
        data = {
            "name": "click",
            "item_type": "pypi",
            "current_version": "8.1.0",
            "added_at": "2026-03-29T10:00:00",
            "last_checked": "2026-03-29T12:00:00",
        }
        item = TrackedItem.from_dict(data)
        assert item.last_checked == datetime(2026, 3, 29, 12, 0, 0)


class TestItemType:
    """Tests for ItemType enum."""

    def test_values(self) -> None:
        assert ItemType.PYPI.value == "pypi"
        assert ItemType.GITHUB.value == "github"
        assert ItemType.TOPIC.value == "topic"

    def test_from_string(self) -> None:
        assert ItemType("pypi") == ItemType.PYPI
        assert ItemType("github") == ItemType.GITHUB


class TestReleaseInfo:
    """Tests for ReleaseInfo dataclass."""

    def test_create_release(self) -> None:
        release = ReleaseInfo(
            package="litellm",
            version="1.41.0",
            published_at=datetime(2026, 3, 28),
            summary="Breaking change in Azure auth flow",
            breaking=True,
            changelog_url="https://github.com/BerriAI/litellm/releases/tag/v1.41.0",
            highlights=["Azure auth flow changed", "New provider support"],
        )
        assert release.package == "litellm"
        assert release.breaking is True
        assert len(release.highlights) == 2

    def test_defaults(self) -> None:
        release = ReleaseInfo(
            package="click",
            version="8.2.0",
            published_at=datetime(2026, 3, 1),
            summary="Minor bugfixes",
        )
        assert release.breaking is False
        assert release.changelog_url == ""
        assert release.highlights == []


class TestTrendingItem:
    """Tests for TrendingItem dataclass."""

    def test_create_trending(self) -> None:
        item = TrendingItem(
            title="hermes-agent",
            source="github",
            url="https://github.com/NousResearch/hermes-agent",
            score=15000,
            description="The agent that grows with you",
        )
        assert item.source == "github"
        assert item.score == 15000
        assert item.relevance is None


class TestBriefingItem:
    """Tests for BriefingItem dataclass."""

    def test_priority_emoji(self) -> None:
        critical = BriefingItem(
            priority=Priority.CRITICAL,
            category=BriefingCategory.RELEASE,
            title="litellm 1.41.0",
            body="Breaking change",
        )
        assert critical.priority_emoji == "🔴"

        important = BriefingItem(
            priority=Priority.IMPORTANT,
            category=BriefingCategory.TRENDING,
            title="hermes-agent trending",
            body="15K stars",
        )
        assert important.priority_emoji == "🟡"

        fyi = BriefingItem(
            priority=Priority.FYI,
            category=BriefingCategory.NEWS,
            title="pytest 9.0.2",
            body="Minor update",
        )
        assert fyi.priority_emoji == "🟢"

    def test_defaults(self) -> None:
        item = BriefingItem(
            priority=Priority.FYI,
            category=BriefingCategory.NEWS,
            title="test",
            body="body",
        )
        assert item.source_url == ""
        assert item.ai_insight is None
        assert item.relevance_score == 0.0


class TestBriefing:
    """Tests for Briefing dataclass."""

    def _make_briefing(self) -> Briefing:
        return Briefing(
            generated_at=datetime(2026, 3, 29, 12, 0, 0),
            tracked_count=5,
            model_used="azure/gpt-4.1",
            items=[
                BriefingItem(
                    priority=Priority.CRITICAL,
                    category=BriefingCategory.RELEASE,
                    title="litellm 1.41.0",
                    body="Breaking: Azure auth changed",
                ),
                BriefingItem(
                    priority=Priority.IMPORTANT,
                    category=BriefingCategory.TRENDING,
                    title="hermes-agent",
                    body="15K stars this week",
                ),
                BriefingItem(
                    priority=Priority.FYI,
                    category=BriefingCategory.NEWS,
                    title="pytest 9.0.2",
                    body="Minor bugfixes",
                ),
                BriefingItem(
                    priority=Priority.FYI,
                    category=BriefingCategory.NEWS,
                    title="ruff 0.15.0",
                    body="New rules",
                ),
            ],
        )

    def test_filter_by_priority(self) -> None:
        briefing = self._make_briefing()
        assert len(briefing.critical_items) == 1
        assert len(briefing.important_items) == 1
        assert len(briefing.fyi_items) == 2

    def test_to_json(self) -> None:
        briefing = self._make_briefing()
        json_str = briefing.to_json()
        data = json.loads(json_str)
        assert data["tracked_count"] == 5
        assert data["model_used"] == "azure/gpt-4.1"
        assert data["generated_at"] == "2026-03-29T12:00:00"
        assert len(data["items"]) == 4
        assert data["items"][0]["priority"] == "critical"
        assert data["items"][0]["category"] == "release"

    def test_to_json_no_model(self) -> None:
        briefing = Briefing(
            generated_at=datetime(2026, 3, 29),
            tracked_count=0,
        )
        data = json.loads(briefing.to_json())
        assert data["model_used"] is None
        assert data["items"] == []

    def test_empty_briefing(self) -> None:
        briefing = Briefing(
            generated_at=datetime(2026, 3, 29),
            tracked_count=0,
        )
        assert briefing.critical_items == []
        assert briefing.important_items == []
        assert briefing.fyi_items == []
        assert briefing.content_ideas is None
