"""Unit tests for the StarMaker command modules.

Covers the structural refactor of the ``starmaker.commands`` package:
draft generation, comparison/readme/awesome output, case-insensitive tag
matching, explicit-unknown-platform handling, and write-error resilience.

No network or live posting is exercised. Rich console output is redirected to
an in-memory buffer per module to avoid Windows I/O teardown errors.
"""

from __future__ import annotations

import io
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from rich.console import Console

from starmaker.config import (
    ProjectConfig,
    PromotionConfig,
    StarMakerConfig,
)
from starmaker.commands import _constants


@contextmanager
def silence(module_name: str):
    """Patch ``<module>.console`` with a quiet in-memory console."""
    quiet = Console(file=io.StringIO(), force_terminal=False)
    with patch(f"{module_name}.console", quiet):
        yield


def _sample_config() -> StarMakerConfig:
    """Build a representative config equivalent to starmaker.example.yaml."""
    return StarMakerConfig(
        project=ProjectConfig(
            name="MyProject",
            repo="https://github.com/username/my-project",
            tagline="A one-line description of your project",
            description="A longer description explaining what this does.",
            competitors=["Competitor1", "Competitor2"],
            tags=["python", "cli", "open-source"],
            highlights=["Feature 1", "Feature 2", "Feature 3"],
            tech_stack=["Python", "Click", "Rich"],
        ),
        promotion=PromotionConfig(
            platforms=["reddit", "hackernews", "devto", "twitter", "discord"],
            reddit={"subreddits": ["opensource", "commandline", "Python"]},
            awesome_lists=["awesome-python", "awesome-cli-apps"],
            comparison={
                "features": ["Feature 1", "Feature 2", "Open Source"],
                "competitors": {
                    "Competitor1": [True, True, False],
                    "Competitor2": [True, False, True],
                },
            },
        ),
    )


# ---------------------------------------------------------------------------
# _constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_label_for_filename_known(self):
        assert _constants.label_for_filename("devto_article.md") == "Dev.to"
        assert _constants.label_for_filename("twitter_single.md") == "Twitter/X"
        assert _constants.label_for_filename("discord.md") == "Discord"
        assert _constants.label_for_filename("hackernews.md") == "Hacker News"
        assert _constants.label_for_filename("reddit_r_python.md") == "Reddit"

    def test_label_for_filename_unknown(self):
        assert _constants.label_for_filename("mystery.md") == "unknown"

    def test_draft_filenames_match_humanizer(self):
        """Constants must agree with the humanizer's actual output filenames."""
        from starmaker.nlp.readme_parser import ReadmeContent
        from starmaker.nlp import humanizer

        content = ReadmeContent(
            title="MyProject",
            tagline="tagline",
            description="desc",
            highlights=["a"],
            tags=["python"],
            tech_stack=["Python"],
            repo_url="https://github.com/u/p",
        )
        assert set(humanizer.humanize_for_devto(content)) == {
            _constants.DRAFT_FILENAMES[_constants.PLATFORM_DEVTO]
        }
        assert set(humanizer.humanize_for_twitter(content)) == {
            _constants.DRAFT_FILENAMES[_constants.PLATFORM_TWITTER]
        }
        assert set(humanizer.humanize_for_discord(content)) == {
            _constants.DRAFT_FILENAMES[_constants.PLATFORM_DISCORD]
        }
        assert set(humanizer.humanize_for_hackernews(content)) == {
            _constants.DRAFT_FILENAMES[_constants.PLATFORM_HACKERNEWS]
        }
        reddit = humanizer.humanize_for_reddit(content, ["python"])
        assert all(
            name.startswith(_constants.REDDIT_DRAFT_PREFIX) for name in reddit
        )


# ---------------------------------------------------------------------------
# draft_posts
# ---------------------------------------------------------------------------


class TestDraftPosts:
    def test_generates_expected_filenames(self, tmp_path):
        from starmaker.commands import draft_posts

        out = tmp_path / "drafts"
        with silence("starmaker.commands.draft_posts"):
            draft_posts.run(_sample_config(), output_dir=str(out))

        filenames = {f.name for f in out.glob("*.md")}
        assert _constants.DRAFT_FILENAMES[_constants.PLATFORM_DEVTO] in filenames
        assert _constants.DRAFT_FILENAMES[_constants.PLATFORM_TWITTER] in filenames
        assert _constants.DRAFT_FILENAMES[_constants.PLATFORM_DISCORD] in filenames
        assert _constants.DRAFT_FILENAMES[_constants.PLATFORM_HACKERNEWS] in filenames
        assert any(n.startswith(_constants.REDDIT_DRAFT_PREFIX) for n in filenames)

    def test_single_platform_filter(self, tmp_path):
        from starmaker.commands import draft_posts

        out = tmp_path / "drafts"
        with silence("starmaker.commands.draft_posts"):
            draft_posts.run(_sample_config(), platform="twitter", output_dir=str(out))

        filenames = {f.name for f in out.glob("*.md")}
        # The twitter generator may emit single + thread drafts; all are twitter.
        assert _constants.DRAFT_FILENAMES[_constants.PLATFORM_TWITTER] in filenames
        assert all(name.startswith("twitter") for name in filenames)

    def test_explicit_unknown_platform_fails_loudly(self, tmp_path):
        """An explicit unknown --platform prints an error and writes nothing."""
        from starmaker.commands import draft_posts

        out = tmp_path / "drafts"
        buf = io.StringIO()
        quiet = Console(file=buf, force_terminal=False)
        with patch("starmaker.commands.draft_posts.console", quiet):
            draft_posts.run(_sample_config(), platform="fakeplatform", output_dir=str(out))

        # Clear error mentioning the bad platform, and no files written.
        output = buf.getvalue()
        assert "fakeplatform" in output
        assert "Unknown platform" in output
        assert not out.exists() or list(out.glob("*.md")) == []

    def test_no_project_configured(self, tmp_path):
        from starmaker.commands import draft_posts

        out = tmp_path / "drafts"
        with silence("starmaker.commands.draft_posts"):
            draft_posts.run(StarMakerConfig(), output_dir=str(out))
        assert not out.exists()

    def test_write_error_is_handled(self, tmp_path):
        """A write failure is reported, not raised, and other drafts continue."""
        from starmaker.commands import draft_posts

        out = tmp_path / "drafts"
        real_write = type(out).write_text
        calls = {"n": 0}

        def flaky_write(self, *args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("disk full")
            return real_write(self, *args, **kwargs)

        with silence("starmaker.commands.draft_posts"), patch(
            "pathlib.Path.write_text", flaky_write
        ):
            # Should not raise despite the first write failing.
            draft_posts.run(_sample_config(), platform="twitter", output_dir=str(out))

        # The twitter generator emits two drafts; the first write raised OSError
        # but the loop must continue and write the second, proving resilience.
        assert calls["n"] >= 2
        written = {f.name for f in out.glob("*.md")}
        assert _constants.DRAFT_FILENAMES[_constants.PLATFORM_TWITTER] in written


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------


class TestCompare:
    def test_generates_comparison_table(self, tmp_path):
        from starmaker.commands import compare

        out = tmp_path / "drafts"
        with silence("starmaker.commands.compare"):
            compare.run(_sample_config(), output_dir=str(out))

        comparison = out / "comparison.md"
        assert comparison.exists()
        text = comparison.read_text(encoding="utf-8")
        assert "Feature Comparison" in text
        assert "MyProject" in text
        assert "Competitor1" in text
        assert "Competitor2" in text

    def test_no_competitors_warns(self, tmp_path):
        from starmaker.commands import compare

        cfg = StarMakerConfig(project=ProjectConfig(name="P"))
        out = tmp_path / "drafts"
        with silence("starmaker.commands.compare"):
            compare.run(cfg, output_dir=str(out))
        assert not (out / "comparison.md").exists()


# ---------------------------------------------------------------------------
# readme
# ---------------------------------------------------------------------------


class TestReadme:
    def test_generates_suggestions(self, tmp_path):
        from starmaker.commands import readme

        readme_file = tmp_path / "README.md"
        readme_file.write_text("# MyProject\n\nA tool.\n", encoding="utf-8")
        out = tmp_path / "drafts"

        with silence("starmaker.commands.readme"):
            readme.run(
                _sample_config(),
                readme_path=str(readme_file),
                output_dir=str(out),
            )

        suggestions = out / "readme_suggestions.md"
        # A sparse README should yield suggestions.
        assert suggestions.exists()
        text = suggestions.read_text(encoding="utf-8")
        assert "README Enhancement Suggestions" in text


# ---------------------------------------------------------------------------
# awesome
# ---------------------------------------------------------------------------


class TestAwesome:
    def test_matches_lists_from_tags(self, tmp_path):
        from starmaker.commands import awesome

        out = tmp_path / "drafts"
        with silence("starmaker.commands.awesome"):
            awesome.run(_sample_config(), output_dir=str(out))

        pr_dir = out / "awesome-lists"
        assert pr_dir.exists()
        files = list(pr_dir.glob("pr_*.md"))
        assert files  # python + cli + open-source tags all map to lists

    def test_tag_matching_is_case_insensitive(self):
        from starmaker.commands import awesome

        lower = awesome._find_matching_lists(
            StarMakerConfig(project=ProjectConfig(name="P", tags=["python"]))
        )
        upper = awesome._find_matching_lists(
            StarMakerConfig(project=ProjectConfig(name="P", tags=["Python"]))
        )
        mixed = awesome._find_matching_lists(
            StarMakerConfig(project=ProjectConfig(name="P", tags=["PYTHON"]))
        )
        assert lower == upper == mixed
        assert lower  # python definitely matches awesome-python

    def test_no_tags_no_matches(self, tmp_path):
        from starmaker.commands import awesome

        out = tmp_path / "drafts"
        with silence("starmaker.commands.awesome"):
            awesome.run(
                StarMakerConfig(project=ProjectConfig(name="P")),
                output_dir=str(out),
            )
        assert not (out / "awesome-lists").exists()


# ---------------------------------------------------------------------------
# post (parsing only — no network)
# ---------------------------------------------------------------------------


class TestPostParsing:
    def test_drafts_roundtrip_through_post_parsers(self, tmp_path):
        """Drafts generated by draft_posts parse cleanly in post.py."""
        from starmaker.commands import draft_posts
        from starmaker.commands import post

        out = tmp_path / "drafts"
        with silence("starmaker.commands.draft_posts"):
            draft_posts.run(_sample_config(), output_dir=str(out))

        devto = out / _constants.DRAFT_FILENAMES[_constants.PLATFORM_DEVTO]
        title, body, tags = post._parse_devto_draft(devto)
        assert title and body

        twitter = out / _constants.DRAFT_FILENAMES[_constants.PLATFORM_TWITTER]
        assert post._parse_twitter_single(twitter)

        reddit_files = list(out.glob(_constants.REDDIT_DRAFT_GLOB))
        assert reddit_files
        r_title, r_body, subreddit = post._parse_reddit_draft(reddit_files[0])
        assert r_title and r_body and subreddit
