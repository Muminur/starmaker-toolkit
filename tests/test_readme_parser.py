"""Tests for the README parser module."""

from __future__ import annotations


from starmaker.nlp.readme_parser import (
    _extract_keywords,
    _score_sentences,
    build_config_from_readme,
    get_top_sentences,
    parse_readme,
)

SAMPLE_README = """# MuttonText

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](#platform-support)

**Free, open-source, cross-platform text expansion for Linux and macOS**

MuttonText is a privacy-first text snippet expansion tool that automates repetitive typing through intelligent keyword-to-snippet substitution. Built with native performance and Beeftext compatibility, MuttonText brings powerful text expansion to Linux and macOS users.

## Key Features

- **Privacy First** - All data stays local. No telemetry. No cloud. Ever.
- **Native Performance** - Sub-50ms substitution latency through Rust backend
- **Beeftext Compatible** - Import/export Beeftext libraries seamlessly
- **Rich Variables** - Date/time, clipboard, input dialogs, nested combos

## Quick Start

```bash
curl -sL https://api.github.com/repos/Muminur/MuttonText/releases/latest ...
```

Type `hello` followed by a space in any application.

## Build from Source

### Prerequisites
- Rust 1.78+
- Node.js 18+

## License

MuttonText is licensed under the MIT License.
"""


class TestReadmeParser:
    """Tests for the main parse_readme function."""

    def test_extract_title(self) -> None:
        content = parse_readme(SAMPLE_README)
        assert content.title == "MuttonText"

    def test_extract_tagline(self) -> None:
        content = parse_readme(SAMPLE_README)
        assert content.tagline == "Free, open-source, cross-platform text expansion for Linux and macOS"

    def test_extract_description(self) -> None:
        content = parse_readme(SAMPLE_README)
        assert content.description.startswith("MuttonText is a privacy-first")
        assert "keyword-to-snippet substitution" in content.description

    def test_extract_sections(self) -> None:
        content = parse_readme(SAMPLE_README)
        assert "Key Features" in content.sections
        assert "Quick Start" in content.sections
        assert "Build from Source" in content.sections
        assert "License" in content.sections

    def test_skip_badges(self) -> None:
        content = parse_readme(SAMPLE_README)
        # Badges should not appear in description or tagline
        assert "img.shields.io" not in content.description
        assert "img.shields.io" not in content.tagline
        assert "[![" not in content.description

    def test_skip_code_blocks(self) -> None:
        content = parse_readme(SAMPLE_README)
        # Code block content should not appear in sections
        quick_start = content.sections.get("Quick Start", "")
        assert "curl -sL" not in quick_start

    def test_extract_highlights(self) -> None:
        content = parse_readme(SAMPLE_README)
        assert len(content.highlights) == 4
        assert any("Privacy First" in h for h in content.highlights)
        assert any("Native Performance" in h for h in content.highlights)

    def test_highlight_strips_bold_markers(self) -> None:
        content = parse_readme(SAMPLE_README)
        for highlight in content.highlights:
            assert "**" not in highlight

    def test_extract_repo_url(self) -> None:
        # The sample README only has api.github.com URLs inside code blocks,
        # which get filtered. Test with an explicit repo link instead.
        readme_with_repo = SAMPLE_README + "\nCheck out https://github.com/Muminur/MuttonText for more.\n"
        content = parse_readme(readme_with_repo)
        assert content.repo_url == "https://github.com/Muminur/MuttonText"

    def test_extract_tags_from_content(self) -> None:
        content = parse_readme(SAMPLE_README)
        assert "rust" in content.tags
        assert "linux" in content.tags
        assert "macos" in content.tags
        assert "privacy" in content.tags
        assert "open-source" in content.tags

    def test_empty_readme(self) -> None:
        content = parse_readme("")
        assert content.title == ""
        assert content.tagline == ""
        assert content.description == ""
        assert content.sections == {}
        assert content.highlights == []
        assert content.tags == []

    def test_minimal_readme(self) -> None:
        content = parse_readme("# MyProject\n")
        assert content.title == "MyProject"
        assert content.tagline == ""
        assert content.description == ""
        assert content.sections == {}
        assert content.highlights == []


class TestSentenceScorer:
    """Tests for sentence scoring logic."""

    def test_scores_first_sentences_higher(self) -> None:
        text = "First sentence here. Second sentence here. Third sentence here and more."
        scored = _score_sentences(text)
        # First sentence should have higher score than last
        first_score = next(s for s, t in scored if "First" in t)
        third_score = next(s for s, t in scored if "Third" in t)
        assert first_score > third_score

    def test_scores_sentences_with_project_name_higher(self) -> None:
        text = "Generic sentence about things. MuttonText is a great tool for productivity."
        scored = _score_sentences(text, project_name="MuttonText")
        top_sentence = scored[0][1]
        assert "MuttonText" in top_sentence

    def test_skips_short_sentences(self) -> None:
        text = "OK. This is a much longer and more informative sentence about the project."
        scored = _score_sentences(text)
        short_score = next(s for s, t in scored if t == "OK.")
        long_score = next(s for s, t in scored if "longer" in t)
        assert long_score > short_score

    def test_returns_top_n_sentences(self) -> None:
        text = (
            "First sentence is here. Second sentence is here. "
            "Third sentence is here. Fourth sentence is here."
        )
        result = get_top_sentences(text, n=3)
        assert len(result) == 3


class TestKeywordExtractor:
    """Tests for keyword extraction."""

    def test_extracts_frequent_words(self) -> None:
        text = "rust rust rust python python linux"
        keywords = _extract_keywords(text, max_count=5)
        assert keywords[0] == "rust"
        assert "python" in keywords

    def test_filters_stopwords(self) -> None:
        text = "the a is are was were and or but not this that with from"
        keywords = _extract_keywords(text, max_count=10)
        assert len(keywords) == 0

    def test_returns_limited_count(self) -> None:
        text = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
        keywords = _extract_keywords(text, max_count=3)
        assert len(keywords) == 3


class TestBuildConfig:
    """Tests for building StarMakerConfig from README."""

    def test_build_config_from_readme(self) -> None:
        config = build_config_from_readme(SAMPLE_README)
        assert config is not None
        assert config.project is not None
        assert config.promotion is not None

    def test_config_has_name(self) -> None:
        config = build_config_from_readme(SAMPLE_README)
        assert config.project.name == "MuttonText"

    def test_config_has_tagline(self) -> None:
        config = build_config_from_readme(SAMPLE_README)
        assert config.project.tagline == "Free, open-source, cross-platform text expansion for Linux and macOS"

    def test_config_has_highlights(self) -> None:
        config = build_config_from_readme(SAMPLE_README)
        assert len(config.project.highlights) == 4
        assert any("Privacy First" in h for h in config.project.highlights)

    def test_config_has_tags(self) -> None:
        config = build_config_from_readme(SAMPLE_README)
        assert "rust" in config.project.tags
        assert "linux" in config.project.tags

    def test_config_has_repo(self) -> None:
        config = build_config_from_readme(SAMPLE_README, repo_url="https://github.com/Muminur/MuttonText")
        assert config.project.repo == "https://github.com/Muminur/MuttonText"

    def test_config_default_subreddits(self) -> None:
        config = build_config_from_readme(SAMPLE_README)
        subreddits = config.promotion.reddit.get("subreddits", [])
        assert "rust" in subreddits
        assert "linux" in subreddits
        assert "privacy" in subreddits
