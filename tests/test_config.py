"""Tests for the StarMaker configuration loader.

Covers:
  * Loading a valid starmaker.yaml into dataclasses.
  * The empty-default path (no config file -> empty StarMakerConfig, no error).
  * Validation: non-empty project name + well-formed repo URL, surfaced as a
    user-facing ConfigError (a click.ClickException) rather than a traceback.
  * Mutable-default safety for the dataclasses.
  * detect_local_repo logging behaviour when git is unavailable.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import click
import pytest
import yaml

from starmaker.config import (
    AuthorConfig,
    ConfigError,
    PromotionConfig,
    ProjectConfig,
    StarMakerConfig,
    _is_valid_repo_url,
    detect_local_repo,
    find_config,
    load_config,
)


VALID_RAW = {
    "project": {
        "name": "MyProject",
        "repo": "https://github.com/owner/my-project",
        "tagline": "A neat tool",
        "description": "  Longer description.  ",
        "website": "https://example.com",
        "competitors": ["A", "B"],
        "tags": ["python", "cli"],
        "highlights": ["fast", "free"],
        "tech_stack": ["Python", "Click"],
    },
    "author": {
        "name": "Jane",
        "github": "jane",
        "twitter": "",
        "website": "",
    },
    "promotion": {
        "platforms": ["reddit", "devto"],
        "reddit": {"subreddits": ["python"]},
        "awesome_lists": ["awesome-python"],
        "comparison": {"features": ["Free"]},
    },
}


def _write_config(tmp_path: Path, raw: dict) -> Path:
    path = tmp_path / "starmaker.yaml"
    path.write_text(yaml.dump(raw), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# TestDefaults
# ---------------------------------------------------------------------------

class TestDefaults:
    """Empty / missing config must not raise and must yield safe defaults."""

    def test_missing_file_returns_empty_config(self, tmp_path):
        """An explicit non-existent path returns an empty default config."""
        config = load_config(tmp_path / "nope.yaml")
        assert isinstance(config, StarMakerConfig)
        assert config.project.name == ""
        assert config.promotion.platforms  # default platforms populated

    def test_no_config_found_returns_empty_config(self, tmp_path, monkeypatch):
        """When find_config locates nothing, an empty config is returned."""
        monkeypatch.chdir(tmp_path)
        config = load_config()
        assert isinstance(config, StarMakerConfig)
        assert config.project.name == ""

    def test_empty_yaml_file_returns_empty_config(self, tmp_path):
        """A whitespace-only / empty YAML file is not an error."""
        path = tmp_path / "starmaker.yaml"
        path.write_text("\n", encoding="utf-8")
        config = load_config(path)
        assert config.project.name == ""

    def test_default_config_has_independent_mutable_fields(self):
        """Mutable defaults must not be shared between instances (no aliasing)."""
        a = StarMakerConfig()
        b = StarMakerConfig()
        a.project.tags.append("leaked")
        assert b.project.tags == []
        a.promotion.platforms.append("leaked")
        assert "leaked" not in b.promotion.platforms

    def test_project_config_default_lists_independent(self):
        p1 = ProjectConfig()
        p2 = ProjectConfig()
        p1.competitors.append("x")
        assert p2.competitors == []


# ---------------------------------------------------------------------------
# TestValidLoad
# ---------------------------------------------------------------------------

class TestValidLoad:
    """A complete, valid config loads into the dataclasses correctly."""

    def test_loads_project_fields(self, tmp_path):
        path = _write_config(tmp_path, VALID_RAW)
        config = load_config(path)
        assert config.project.name == "MyProject"
        assert config.project.repo == "https://github.com/owner/my-project"
        assert config.project.description == "Longer description."  # stripped
        assert config.project.tags == ["python", "cli"]

    def test_loads_author_and_promotion(self, tmp_path):
        path = _write_config(tmp_path, VALID_RAW)
        config = load_config(path)
        assert config.author.name == "Jane"
        assert config.promotion.platforms == ["reddit", "devto"]
        assert config.promotion.reddit == {"subreddits": ["python"]}

    def test_ssh_repo_url_is_valid(self, tmp_path):
        raw = {"project": {"name": "P", "repo": "git@github.com:owner/repo.git"}}
        path = _write_config(tmp_path, raw)
        config = load_config(path)
        assert config.project.repo == "git@github.com:owner/repo.git"

    def test_self_hosted_https_repo_is_valid(self, tmp_path):
        raw = {"project": {"name": "P", "repo": "https://gitlab.example.com/o/r"}}
        path = _write_config(tmp_path, raw)
        assert load_config(path).project.repo == "https://gitlab.example.com/o/r"

    def test_empty_repo_is_allowed(self, tmp_path):
        """A name with no repo is valid (repo is optional)."""
        raw = {"project": {"name": "P", "repo": ""}}
        path = _write_config(tmp_path, raw)
        assert load_config(path).project.name == "P"


# ---------------------------------------------------------------------------
# TestValidation
# ---------------------------------------------------------------------------

class TestValidation:
    """Invalid config raises a clean, user-facing ConfigError (no traceback)."""

    def test_config_error_is_click_exception(self):
        """ConfigError must render as a clean CLI error, not a traceback."""
        assert issubclass(ConfigError, click.ClickException)

    def test_missing_name_raises(self, tmp_path):
        raw = {"project": {"repo": "https://github.com/owner/repo"}}
        path = _write_config(tmp_path, raw)
        with pytest.raises(ConfigError) as exc:
            load_config(path)
        assert "name" in str(exc.value).lower()

    def test_blank_name_raises(self, tmp_path):
        raw = {"project": {"name": "   ", "repo": "https://github.com/o/r"}}
        path = _write_config(tmp_path, raw)
        with pytest.raises(ConfigError):
            load_config(path)

    def test_malformed_repo_url_raises(self, tmp_path):
        raw = {"project": {"name": "P", "repo": "not a url"}}
        path = _write_config(tmp_path, raw)
        with pytest.raises(ConfigError) as exc:
            load_config(path)
        assert "repo" in str(exc.value).lower() or "url" in str(exc.value).lower()

    def test_scheme_only_repo_raises(self, tmp_path):
        """A scheme without a host (e.g. 'ftp://') is rejected."""
        raw = {"project": {"name": "P", "repo": "ftp://example.com/r"}}
        path = _write_config(tmp_path, raw)
        with pytest.raises(ConfigError):
            load_config(path)

    def test_top_level_not_mapping_raises(self, tmp_path):
        path = tmp_path / "starmaker.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")
        with pytest.raises(ConfigError):
            load_config(path)

    def test_project_section_not_mapping_raises(self, tmp_path):
        path = tmp_path / "starmaker.yaml"
        path.write_text("project: just-a-string\n", encoding="utf-8")
        with pytest.raises(ConfigError):
            load_config(path)

    def test_error_message_has_no_traceback_markers(self, tmp_path):
        """The message should read as user guidance, mentioning the file."""
        raw = {"project": {"name": "P", "repo": "garbage"}}
        path = _write_config(tmp_path, raw)
        with pytest.raises(ConfigError) as exc:
            load_config(path)
        assert "starmaker.yaml" in str(exc.value)


# ---------------------------------------------------------------------------
# TestRepoUrlValidator
# ---------------------------------------------------------------------------

class TestRepoUrlValidator:
    """Unit tests for the _is_valid_repo_url helper."""

    @pytest.mark.parametrize("url", [
        "https://github.com/owner/repo",
        "http://example.com/o/r",
        "https://gitlab.example.com/group/sub/repo",
        "git@github.com:owner/repo.git",
        "git@gitlab.com:owner/repo",
    ])
    def test_valid_urls(self, url):
        assert _is_valid_repo_url(url) is True

    @pytest.mark.parametrize("url", [
        "not a url",
        "ftp://example.com/r",
        "github.com/owner/repo",  # no scheme
        "https://",               # no netloc
        "",
    ])
    def test_invalid_urls(self, url):
        assert _is_valid_repo_url(url) is False


# ---------------------------------------------------------------------------
# TestFindConfig
# ---------------------------------------------------------------------------

class TestFindConfig:
    """find_config walks up parent directories."""

    def test_finds_in_current_dir(self, tmp_path):
        (tmp_path / "starmaker.yaml").write_text("project: {}\n", encoding="utf-8")
        assert find_config(tmp_path) == tmp_path / "starmaker.yaml"

    def test_finds_in_parent_dir(self, tmp_path):
        (tmp_path / "starmaker.yaml").write_text("project: {}\n", encoding="utf-8")
        child = tmp_path / "a" / "b"
        child.mkdir(parents=True)
        assert find_config(child) == tmp_path / "starmaker.yaml"

    def test_returns_none_when_absent(self, tmp_path):
        assert find_config(tmp_path) is None


# ---------------------------------------------------------------------------
# TestDetectLocalRepo
# ---------------------------------------------------------------------------

class TestDetectLocalRepo:
    """detect_local_repo parses git output and logs (not raises) on failure."""

    def test_parses_https_remote(self, monkeypatch):
        def fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(
                args, 0, stdout="https://github.com/owner/repo.git\n", stderr=""
            )
        monkeypatch.setattr(subprocess, "run", fake_run)
        info = detect_local_repo()
        assert info["repo"] == "https://github.com/owner/repo"
        assert info["owner"] == "owner"
        assert info["name"] == "repo"

    def test_converts_ssh_remote(self, monkeypatch):
        def fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(
                args, 0, stdout="git@github.com:owner/repo.git\n", stderr=""
            )
        monkeypatch.setattr(subprocess, "run", fake_run)
        info = detect_local_repo()
        assert info["repo"] == "https://github.com/owner/repo"

    def test_git_missing_logs_warning_and_returns_empty(self, monkeypatch, caplog):
        def fake_run(*args, **kwargs):
            raise FileNotFoundError("git")
        monkeypatch.setattr(subprocess, "run", fake_run)
        with caplog.at_level("WARNING"):
            info = detect_local_repo()
        assert info == {}
        assert any("git" in r.message.lower() for r in caplog.records)

    def test_git_timeout_logs_warning_and_returns_empty(self, monkeypatch, caplog):
        def fake_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="git", timeout=5)
        monkeypatch.setattr(subprocess, "run", fake_run)
        with caplog.at_level("WARNING"):
            info = detect_local_repo()
        assert info == {}
        assert caplog.records  # a warning was logged

    def test_nonzero_returncode_returns_empty(self, monkeypatch):
        def fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(args, 128, stdout="", stderr="err")
        monkeypatch.setattr(subprocess, "run", fake_run)
        assert detect_local_repo() == {}
