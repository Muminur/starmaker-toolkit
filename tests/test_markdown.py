"""Unit tests for starmaker.utils.markdown."""

from __future__ import annotations

import pytest

from starmaker.utils.markdown import (
    _escape,
    make_badge,
    make_github_badges,
    make_section,
    make_table,
)


class TestMakeTable:
    def test_basic_table(self):
        out = make_table(["A", "B"], [["1", "2"], ["3", "4"]])
        lines = out.splitlines()
        assert lines[0] == "| A | B |"
        assert lines[1] == "| --- | --- |"
        assert lines[2] == "| 1 | 2 |"
        assert lines[3] == "| 3 | 4 |"

    def test_empty_headers_returns_empty(self):
        assert make_table([], [["1"]]) == ""

    def test_empty_rows_returns_empty(self):
        assert make_table(["A"], []) == ""

    def test_short_row_is_padded(self):
        out = make_table(["A", "B", "C"], [["1"]])
        assert out.splitlines()[-1] == "| 1 |  |  |"

    def test_row_wider_than_headers_raises(self):
        with pytest.raises(ValueError) as exc:
            make_table(["A", "B"], [["1", "2", "3"]])
        assert "3 cells" in str(exc.value)
        assert "2 column" in str(exc.value)

    def test_exact_width_row_ok(self):
        out = make_table(["A", "B"], [["1", "2"]])
        assert out.splitlines()[-1] == "| 1 | 2 |"


class TestEscape:
    def test_dash_doubled(self):
        assert _escape("a-b") == "a--b"

    def test_underscore_doubled(self):
        assert _escape("a_b") == "a__b"

    def test_space_to_single_underscore(self):
        assert _escape("a b") == "a_b"

    def test_combined(self):
        # "build-test pass_now"
        # - -> --, _ -> __, space -> _
        assert _escape("build-test pass_now") == "build--test_pass__now"

    def test_non_string_coerced(self):
        assert _escape(42) == "42"

    def test_plain_text_unchanged(self):
        assert _escape("hello") == "hello"


class TestMakeBadge:
    def test_basic_badge(self):
        out = make_badge("coverage", "95%", "green")
        assert out == "![coverage](https://img.shields.io/badge/coverage-95%-green)"

    def test_badge_with_url(self):
        out = make_badge("build", "passing", "blue", url="https://example.com")
        assert out.startswith("[![build]")
        assert out.endswith("(https://example.com)")

    def test_badge_escapes_label_and_value(self):
        out = make_badge("py-version", "3 11")
        assert "py--version-3_11" in out


class TestMakeGithubBadges:
    def test_returns_five_badges(self):
        badges = make_github_badges("owner", "repo")
        assert len(badges) == 5
        assert all("owner/repo" in b for b in badges)

    def test_contains_expected_kinds(self):
        joined = "\n".join(make_github_badges("o", "r"))
        for kind in ("stars", "forks", "license", "release", "issues"):
            assert kind in joined


class TestMakeSection:
    def test_default_level(self):
        assert make_section("Title", "body") == "## Title\n\nbody"

    def test_custom_level(self):
        assert make_section("T", "b", level=3) == "### T\n\nb"
