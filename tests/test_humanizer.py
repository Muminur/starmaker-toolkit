"""Tests for platform-specific post humanizer."""

from __future__ import annotations

import re

import pytest

from starmaker.nlp.readme_parser import ReadmeContent
from starmaker.nlp.humanizer import (
    humanize_for_reddit,
    humanize_for_devto,
    humanize_for_twitter,
    humanize_for_discord,
    humanize_for_hackernews,
    generate_all_drafts,
)

CORPORATE_WORDS = [
    "leverage", "synergy", "innovative solution", "cutting-edge",
    "paradigm", "disruptive", "best-in-class", "world-class",
]


@pytest.fixture
def sample_content():
    return ReadmeContent(
        title="MuttonText",
        tagline="Free, open-source, cross-platform text expansion for Linux and macOS",
        description=(
            "MuttonText is a privacy-first text snippet expansion tool that "
            "automates repetitive typing through intelligent keyword-to-snippet "
            "substitution."
        ),
        sections={
            "Key Features": (
                "- Privacy First\n"
                "- Native Performance\n"
                "- Beeftext Compatible"
            ),
        },
        highlights=[
            "Privacy First - All data stays local. No telemetry. No cloud. Ever.",
            "Native Performance - Sub-50ms substitution latency through Rust backend",
            "Beeftext Compatible - Import/export Beeftext libraries seamlessly",
            "Rich Variables - Date/time, clipboard, input dialogs, nested combos",
        ],
        repo_url="https://github.com/Muminur/MuttonText",
        tags=["rust", "linux", "macos", "open-source", "privacy"],
        tech_stack=["Rust", "Tauri", "React"],
        raw_text="...",
    )


# ---------------------------------------------------------------------------
# Reddit
# ---------------------------------------------------------------------------
class TestRedditHumanizer:
    """Tests for humanize_for_reddit."""

    def test_generates_reddit_draft_format(self, sample_content: ReadmeContent):
        drafts = humanize_for_reddit(sample_content)
        for filename, content in drafts.items():
            assert "**Title:**" in content
            assert "**Body:**" in content
            # Verify the parser regex can extract title
            title_match = re.search(r"\*\*Title:\*\*\s*(.+)", content)
            assert title_match is not None
            # Verify body is extractable
            body_match = re.search(r"\*\*Body:\*\*\s*\n\n(.+)", content, re.DOTALL)
            assert body_match is not None

    def test_title_under_300_chars(self, sample_content: ReadmeContent):
        drafts = humanize_for_reddit(sample_content)
        for filename, content in drafts.items():
            title_match = re.search(r"\*\*Title:\*\*\s*(.+)", content)
            assert title_match is not None
            assert len(title_match.group(1).strip()) <= 300

    def test_body_has_casual_greeting(self, sample_content: ReadmeContent):
        drafts = humanize_for_reddit(sample_content, subreddits=["opensource"])
        content = drafts["reddit_r_opensource.md"]
        body_match = re.search(r"\*\*Body:\*\*\s*\n\n(.+)", content, re.DOTALL)
        body = body_match.group(1).strip()
        # Should start with a casual greeting mentioning the subreddit
        assert re.search(r"(Hey|Hi|Hello|Sharing|I've been)", body) is not None

    def test_body_includes_repo_link(self, sample_content: ReadmeContent):
        drafts = humanize_for_reddit(sample_content)
        for filename, content in drafts.items():
            assert sample_content.repo_url in content

    def test_body_includes_highlights(self, sample_content: ReadmeContent):
        drafts = humanize_for_reddit(sample_content, subreddits=["opensource"])
        content = drafts["reddit_r_opensource.md"]
        # At least one highlight keyword should appear
        assert any(
            kw in content
            for kw in ["Privacy", "Performance", "Beeftext", "Variables"]
        )

    def test_generates_per_subreddit(self, sample_content: ReadmeContent):
        subs = ["opensource", "rust", "linux"]
        drafts = humanize_for_reddit(sample_content, subreddits=subs)
        for sub in subs:
            key = f"reddit_r_{sub}.md"
            assert key in drafts, f"Missing draft for {sub}"

    def test_no_corporate_language(self, sample_content: ReadmeContent):
        drafts = humanize_for_reddit(sample_content)
        for filename, content in drafts.items():
            lower = content.lower()
            for word in CORPORATE_WORDS:
                assert word not in lower, f"Corporate word '{word}' found in {filename}"

    def test_default_subreddits_when_none(self, sample_content: ReadmeContent):
        drafts = humanize_for_reddit(sample_content)
        # Should produce at least the 3 defaults
        assert len(drafts) >= 3


# ---------------------------------------------------------------------------
# Dev.to
# ---------------------------------------------------------------------------
class TestDevtoHumanizer:
    """Tests for humanize_for_devto."""

    def test_generates_devto_format(self, sample_content: ReadmeContent):
        drafts = humanize_for_devto(sample_content)
        content = drafts["devto_article.md"]
        # Must have YAML frontmatter delimiters
        assert content.startswith("---\n")
        # Count frontmatter delimiters
        parts = content.split("---")
        assert len(parts) >= 3, "Missing YAML frontmatter delimiters"

    def test_frontmatter_has_title(self, sample_content: ReadmeContent):
        drafts = humanize_for_devto(sample_content)
        content = drafts["devto_article.md"]
        fm_match = re.search(r"---\n(.+?)\n---", content, re.DOTALL)
        assert fm_match is not None
        fm = fm_match.group(1)
        assert re.search(r'title:\s*"(.+?)"', fm) is not None

    def test_frontmatter_has_tags(self, sample_content: ReadmeContent):
        drafts = humanize_for_devto(sample_content)
        content = drafts["devto_article.md"]
        fm_match = re.search(r"---\n(.+?)\n---", content, re.DOTALL)
        fm = fm_match.group(1)
        tags_match = re.search(r"tags:\s*(.+)", fm)
        assert tags_match is not None
        tags = [t.strip() for t in tags_match.group(1).split(",")]
        assert len(tags) <= 4

    def test_frontmatter_published_false(self, sample_content: ReadmeContent):
        drafts = humanize_for_devto(sample_content)
        content = drafts["devto_article.md"]
        fm_match = re.search(r"---\n(.+?)\n---", content, re.DOTALL)
        fm = fm_match.group(1)
        assert "published: false" in fm

    def test_body_has_sections(self, sample_content: ReadmeContent):
        drafts = humanize_for_devto(sample_content)
        content = drafts["devto_article.md"]
        assert "## What is" in content or "## What Is" in content
        assert "## Key Features" in content or "## Features" in content
        assert "## Getting Started" in content

    def test_body_is_article_length(self, sample_content: ReadmeContent):
        drafts = humanize_for_devto(sample_content)
        content = drafts["devto_article.md"]
        # Strip frontmatter
        parts = content.split("---", 2)
        body = parts[2] if len(parts) >= 3 else content
        assert len(body.strip()) >= 200


# ---------------------------------------------------------------------------
# Twitter
# ---------------------------------------------------------------------------
class TestTwitterHumanizer:
    """Tests for humanize_for_twitter."""

    def test_generates_twitter_format(self, sample_content: ReadmeContent):
        drafts = humanize_for_twitter(sample_content)
        content = drafts["twitter_single.md"]
        assert content.startswith("# Twitter/X Single Post")
        assert "---" in content

    def test_tweet_under_280_chars(self, sample_content: ReadmeContent):
        drafts = humanize_for_twitter(sample_content)
        content = drafts["twitter_single.md"]
        # Extract tweet text (between header and ---)
        lines = content.split("\n")
        tweet_lines = []
        skip = True
        for line in lines:
            if line.startswith("# "):
                skip = False
                continue
            if line.startswith("---"):
                break
            if not skip:
                tweet_lines.append(line)
        tweet = "\n".join(tweet_lines).strip()
        assert len(tweet) <= 280, f"Tweet is {len(tweet)} chars, exceeds 280"

    def test_includes_repo_link(self, sample_content: ReadmeContent):
        drafts = humanize_for_twitter(sample_content)
        content = drafts["twitter_single.md"]
        assert sample_content.repo_url in content

    def test_includes_hashtags(self, sample_content: ReadmeContent):
        drafts = humanize_for_twitter(sample_content)
        content = drafts["twitter_single.md"]
        assert re.search(r"#\w+", content) is not None


# ---------------------------------------------------------------------------
# Discord
# ---------------------------------------------------------------------------
class TestDiscordHumanizer:
    """Tests for humanize_for_discord."""

    def test_generates_discord_format(self, sample_content: ReadmeContent):
        drafts = humanize_for_discord(sample_content)
        content = drafts["discord.md"]
        # Must have the showcase header that the parser expects
        assert re.search(
            r"\*\*Post this in #showcase.*?\*\*",
            content,
        ) is not None
        assert "---" in content

    def test_includes_highlights(self, sample_content: ReadmeContent):
        drafts = humanize_for_discord(sample_content)
        content = drafts["discord.md"]
        assert any(
            kw in content
            for kw in ["Privacy", "Performance", "Beeftext", "Variables"]
        )

    def test_includes_repo_link(self, sample_content: ReadmeContent):
        drafts = humanize_for_discord(sample_content)
        content = drafts["discord.md"]
        assert sample_content.repo_url in content


# ---------------------------------------------------------------------------
# Hacker News
# ---------------------------------------------------------------------------
class TestHNHumanizer:
    """Tests for humanize_for_hackernews."""

    def test_generates_hn_format(self, sample_content: ReadmeContent):
        drafts = humanize_for_hackernews(sample_content)
        content = drafts["hackernews.md"]
        assert "**Title:**" in content
        assert "**URL:**" in content
        assert re.search(r"\*\*Text \(optional.*?\):\*\*", content) is not None

    def test_title_starts_with_show_hn(self, sample_content: ReadmeContent):
        drafts = humanize_for_hackernews(sample_content)
        content = drafts["hackernews.md"]
        title_match = re.search(r"\*\*Title:\*\*\s*(.+)", content)
        assert title_match is not None
        assert title_match.group(1).strip().startswith("Show HN:")

    def test_title_under_80_chars(self, sample_content: ReadmeContent):
        drafts = humanize_for_hackernews(sample_content)
        content = drafts["hackernews.md"]
        title_match = re.search(r"\*\*Title:\*\*\s*(.+)", content)
        assert title_match is not None
        assert len(title_match.group(1).strip()) <= 80

    def test_body_is_concise(self, sample_content: ReadmeContent):
        drafts = humanize_for_hackernews(sample_content)
        content = drafts["hackernews.md"]
        text_match = re.search(
            r"\*\*Text \(optional.*?\):\*\*\s*\n\n(.+?)(\n---|\Z)",
            content,
            re.DOTALL,
        )
        assert text_match is not None
        body = text_match.group(1).strip()
        # HN bodies should be concise -- under 1500 chars
        assert len(body) < 1500


# ---------------------------------------------------------------------------
# Tone tests
# ---------------------------------------------------------------------------
class TestHumanizeTone:
    """Tests for humanized tone quality."""

    def test_adds_sentence_variation(self, sample_content: ReadmeContent):
        """Calling twice may produce different openings (randomized)."""
        results = set()
        for _ in range(20):
            drafts = humanize_for_reddit(sample_content, subreddits=["test"])
            content = drafts["reddit_r_test.md"]
            body_match = re.search(r"\*\*Body:\*\*\s*\n\n(.+)", content, re.DOTALL)
            first_line = body_match.group(1).split("\n")[0]
            results.add(first_line)
        # With randomization we should see at least 2 different openings in 20 tries
        assert len(results) >= 2, "No variation detected in 20 generations"

    def test_reddit_casual_tone(self, sample_content: ReadmeContent):
        drafts = humanize_for_reddit(sample_content, subreddits=["opensource"])
        content = drafts["reddit_r_opensource.md"].lower()
        for word in CORPORATE_WORDS:
            assert word not in content

    def test_devto_professional_tone(self, sample_content: ReadmeContent):
        drafts = humanize_for_devto(sample_content)
        content = drafts["devto_article.md"]
        # Should have structured article sections
        assert "##" in content

    def test_twitter_concise(self, sample_content: ReadmeContent):
        drafts = humanize_for_twitter(sample_content)
        content = drafts["twitter_single.md"]
        # Extract tweet
        lines = content.split("\n")
        tweet_lines = []
        skip = True
        for line in lines:
            if line.startswith("# "):
                skip = False
                continue
            if line.startswith("---"):
                break
            if not skip:
                tweet_lines.append(line)
        tweet = "\n".join(tweet_lines).strip()
        assert len(tweet) <= 280


# ---------------------------------------------------------------------------
# generate_all_drafts
# ---------------------------------------------------------------------------
class TestGenerateAllDrafts:
    """Tests for the combined generate_all_drafts function."""

    def test_returns_all_platforms(self, sample_content: ReadmeContent):
        drafts = generate_all_drafts(sample_content)
        # Should have at least one of each platform
        filenames = list(drafts.keys())
        assert any(f.startswith("reddit_r_") for f in filenames)
        assert "devto_article.md" in filenames
        assert "twitter_single.md" in filenames
        assert "discord.md" in filenames
        assert "hackernews.md" in filenames

    def test_custom_subreddits(self, sample_content: ReadmeContent):
        drafts = generate_all_drafts(sample_content, subreddits=["python", "rust"])
        assert "reddit_r_python.md" in drafts
        assert "reddit_r_rust.md" in drafts
