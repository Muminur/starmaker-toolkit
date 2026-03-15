"""Integration tests for auto-post command."""
from __future__ import annotations
from unittest.mock import patch
import pytest

SAMPLE_README = """# TestProject

**A simple test project for unit testing**

TestProject is a tool that does testing things. It helps developers test their code quickly and efficiently.

## Key Features

- **Fast Testing** - Run tests in milliseconds
- **Easy Setup** - One command to get started
- **Cross Platform** - Works on Linux, macOS, Windows

## Quick Start

Install with pip install testproject

## License

MIT
"""


class TestAutoPostIntegration:
    @pytest.fixture(autouse=True)
    def silence_console(self):
        """Redirect Rich console output to a StringIO to avoid Windows I/O teardown errors."""
        import io
        from rich.console import Console
        quiet = Console(file=io.StringIO(), force_terminal=False)
        with patch("starmaker.commands.auto_post.console", quiet):
            yield

    def test_generates_all_platform_drafts(self, tmp_path):
        """auto_post generates draft files for all platforms."""
        from starmaker.commands.auto_post import run
        readme_file = tmp_path / "README.md"
        readme_file.write_text(SAMPLE_README)
        output_dir = tmp_path / "drafts"

        run(str(readme_file), repo_url="https://github.com/test/testproject",
            output_dir=str(output_dir), dry_run=True)

        # Check that draft files were created
        files = list(output_dir.glob("*.md"))
        assert len(files) >= 5  # reddit(2+), devto, twitter, discord, hackernews

        # Check specific files exist
        filenames = [f.name for f in files]
        assert "devto_article.md" in filenames
        assert "twitter_single.md" in filenames
        assert "discord.md" in filenames
        assert "hackernews.md" in filenames
        assert any("reddit_r_" in f for f in filenames)

    def test_single_platform_filter(self, tmp_path):
        """--platform flag generates only for that platform."""
        from starmaker.commands.auto_post import run
        readme_file = tmp_path / "README.md"
        readme_file.write_text(SAMPLE_README)
        output_dir = tmp_path / "drafts"

        run(str(readme_file), repo_url="https://github.com/test/testproject",
            platform="twitter", output_dir=str(output_dir), dry_run=True)

        files = list(output_dir.glob("*.md"))
        assert len(files) == 1
        assert files[0].name == "twitter_single.md"

    def test_missing_readme_shows_error(self, tmp_path):
        """Missing README shows error message without crashing."""
        from starmaker.commands.auto_post import run
        run(str(tmp_path / "nonexistent.md"), output_dir=str(tmp_path / "out"))
        # Should not crash; output dir should not be created since we never got past the check
        assert not (tmp_path / "out").exists()

    def test_drafts_parseable_by_post_command(self, tmp_path):
        """Generated drafts can be parsed by the existing post parsers."""
        from starmaker.commands.auto_post import run
        readme_file = tmp_path / "README.md"
        readme_file.write_text(SAMPLE_README)
        output_dir = tmp_path / "drafts"

        run(str(readme_file), repo_url="https://github.com/test/testproject",
            output_dir=str(output_dir), dry_run=True)

        # Try parsing devto draft — _parse_devto_draft takes a Path
        from starmaker.commands.post import _parse_devto_draft
        devto_path = output_dir / "devto_article.md"
        title, body, tags = _parse_devto_draft(devto_path)
        assert title  # non-empty title
        assert body   # non-empty body

        # Try parsing twitter draft — _parse_twitter_single takes a Path
        from starmaker.commands.post import _parse_twitter_single
        twitter_path = output_dir / "twitter_single.md"
        tweet = _parse_twitter_single(twitter_path)
        assert tweet  # non-empty tweet text

    def test_devto_tags_max_four(self, tmp_path):
        """Dev.to draft has at most 4 tags in frontmatter."""
        from starmaker.commands.auto_post import run
        readme_file = tmp_path / "README.md"
        readme_file.write_text(SAMPLE_README)
        output_dir = tmp_path / "drafts"

        run(str(readme_file), repo_url="https://github.com/test/testproject",
            output_dir=str(output_dir), dry_run=True)

        content = (output_dir / "devto_article.md").read_text()
        # Find tags line in frontmatter
        import re
        tags_match = re.search(r'^tags:\s*(.+)$', content, re.MULTILINE)
        if tags_match:
            tags = [t.strip() for t in tags_match.group(1).split(",")]
            assert len(tags) <= 4

    def test_unknown_platform_shows_error(self, tmp_path):
        """Unknown platform name does not crash and shows an error."""
        from starmaker.commands.auto_post import run
        readme_file = tmp_path / "README.md"
        readme_file.write_text(SAMPLE_README)
        output_dir = tmp_path / "drafts"

        # Should not raise
        run(str(readme_file), repo_url="https://github.com/test/testproject",
            platform="fakeplatform", output_dir=str(output_dir), dry_run=True)

        # No files should have been written for an unknown platform
        assert not output_dir.exists() or list(output_dir.glob("*.md")) == []
