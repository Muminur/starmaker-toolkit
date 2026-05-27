"""Tests for the platform draft generators in :mod:`starmaker.platforms`.

These tests guard two things:

1. Each generator returns non-empty content keyed by the expected filename(s).
2. The output keeps the exact format markers that :mod:`starmaker.commands.post`
   relies on when parsing drafts back into postable fields. Changing those
   markers would silently break the round-trip, so they are asserted explicitly.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from starmaker.config import (
    AuthorConfig,
    ProjectConfig,
    PromotionConfig,
    StarMakerConfig,
)
from starmaker.platforms import PLATFORMS
from starmaker.platforms import devto, discord, hackernews, reddit, twitter


@pytest.fixture
def sample_config() -> StarMakerConfig:
    """A fully-populated config exercising every optional branch."""
    return StarMakerConfig(
        project=ProjectConfig(
            name="MyProject",
            repo="https://github.com/user/my-project",
            tagline="A tool that does things",
            description="Does useful things.\nAnd more useful things.",
            website="https://example.com",
            competitors=["Comp1", "Comp2", "Comp3", "Comp4"],
            tags=["python", "rust", "react"],
            highlights=["Highlight one", "Highlight two", "Highlight three"],
            tech_stack=["Python", "Click", "Rich"],
        ),
        author=AuthorConfig(name="Author", github="author", twitter="author"),
        promotion=PromotionConfig(reddit={"subreddits": ["opensource", "Python"]}),
    )


def test_platforms_registry_complete() -> None:
    """All five generators are registered in the PLATFORMS map."""
    assert set(PLATFORMS) == {"reddit", "hackernews", "devto", "twitter", "discord"}
    for func in PLATFORMS.values():
        assert callable(func)


# --- Reddit ----------------------------------------------------------------

def test_reddit_returns_drafts_with_markers(sample_config: StarMakerConfig) -> None:
    drafts = reddit.generate(sample_config)
    assert drafts, "expected at least one reddit draft"
    # Configured subreddits plus tag-derived ones (python->Python dedup, rust, react).
    assert "reddit_r_opensource.md" in drafts
    assert "reddit_r_rust.md" in drafts
    assert "reddit_r_reactjs.md" in drafts
    for name, content in drafts.items():
        assert name.startswith("reddit_r_") and name.endswith(".md")
        assert content.strip()
        assert content.startswith("# Reddit Post for r/")
        assert "**Title:**" in content
        assert "**Body:**" in content


def test_reddit_license_defaults_to_mit(sample_config: StarMakerConfig) -> None:
    """With no license field on the config, the text falls back to MIT."""
    assert reddit._get_license_text(sample_config) == "MIT"
    content = next(iter(reddit.generate(sample_config).values()))
    assert "under the MIT license" in content


def test_reddit_license_read_from_config() -> None:
    """When the project exposes a license attribute, it is used verbatim."""
    cfg = StarMakerConfig(
        project=SimpleNamespace(
            name="P", repo="r", tagline="t", description="d", website="",
            competitors=[], tags=[], highlights=[], tech_stack=[],
            license="Apache-2.0",
        ),
        promotion=PromotionConfig(reddit={"subreddits": ["opensource"]}),
    )
    assert reddit._get_license_text(cfg) == "Apache-2.0"
    content = next(iter(reddit.generate(cfg).values()))
    assert "under the Apache-2.0 license" in content


# --- Hacker News -----------------------------------------------------------

def test_hackernews_markers(sample_config: StarMakerConfig) -> None:
    drafts = hackernews.generate(sample_config)
    assert set(drafts) == {"hackernews.md"}
    content = drafts["hackernews.md"]
    assert content.strip()
    assert content.startswith("# Hacker News")
    assert "**Title:**" in content
    assert "**URL:**" in content
    assert "**Text (optional, for Show HN):**" in content
    assert "Show HN: MyProject" in content


# --- Dev.to ----------------------------------------------------------------

def test_devto_markers(sample_config: StarMakerConfig) -> None:
    drafts = devto.generate(sample_config)
    assert set(drafts) == {"devto_article.md"}
    content = drafts["devto_article.md"]
    assert content.strip()
    assert content.startswith("---\n")
    assert 'title: "Introducing MyProject' in content
    assert "tags:" in content
    assert "## Dev.to Publishing Tips:" in content


# --- Twitter ---------------------------------------------------------------

def test_twitter_markers(sample_config: StarMakerConfig) -> None:
    drafts = twitter.generate(sample_config)
    assert set(drafts) == {"twitter_thread.md", "twitter_single.md"}
    single = drafts["twitter_single.md"]
    assert single.startswith("# Twitter/X Single Post")
    assert "---" in single
    thread = drafts["twitter_thread.md"]
    assert thread.startswith("# Twitter/X Thread")
    assert "**Tweet 1 (Hook):**" in thread


# --- Discord ---------------------------------------------------------------

def test_discord_markers(sample_config: StarMakerConfig) -> None:
    drafts = discord.generate(sample_config)
    assert set(drafts) == {"discord.md"}
    content = drafts["discord.md"]
    assert content.strip()
    assert content.startswith("# Discord Message")
    assert "**Post this in #showcase or #projects channels:**" in content
    assert "## Suggested Discord Servers:" in content


# --- Empty / minimal config ------------------------------------------------

def test_generators_handle_minimal_config() -> None:
    """Generators must not crash on a default (mostly empty) config."""
    cfg = StarMakerConfig()
    for func in PLATFORMS.values():
        drafts = func(cfg)
        assert isinstance(drafts, dict)
        assert drafts
        for content in drafts.values():
            assert isinstance(content, str)
            assert content.strip()
