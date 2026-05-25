"""Configuration loader for StarMaker."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import click
import yaml

logger = logging.getLogger(__name__)


class ConfigError(click.ClickException):
    """Raised on invalid configuration.

    Subclasses ``click.ClickException`` so the CLI prints a clean
    ``Error: <message>`` and exits with a non-zero status instead of dumping
    a Python traceback.
    """


@dataclass
class ProjectConfig:
    """Project configuration loaded from the ``project:`` section of starmaker.yaml."""

    name: str = ""
    """Human-readable project name (required when a config file is present)."""

    repo: str = ""
    """Repository URL, e.g. ``https://github.com/owner/name`` or an ``git@`` SSH URL."""

    tagline: str = ""
    """One-line summary used as a headline in generated posts."""

    description: str = ""
    """Longer multi-sentence description of the project."""

    website: str = ""
    """Optional project/landing-page URL."""

    competitors: list[str] = field(default_factory=list)
    """Names of comparable/competing projects, used for comparison content."""

    tags: list[str] = field(default_factory=list)
    """Topic tags/keywords (e.g. languages, domains) for targeting."""

    highlights: list[str] = field(default_factory=list)
    """Key selling points or notable features."""

    tech_stack: list[str] = field(default_factory=list)
    """Technologies the project is built with."""


@dataclass
class AuthorConfig:
    """Author configuration."""

    name: str = ""
    github: str = ""
    twitter: str = ""
    website: str = ""


@dataclass
class PromotionConfig:
    """Promotion settings."""

    platforms: list[str] = field(default_factory=lambda: [
        "reddit", "hackernews", "devto", "twitter", "discord"
    ])
    reddit: dict[str, Any] = field(default_factory=dict)
    awesome_lists: list[str] = field(default_factory=list)
    comparison: dict[str, Any] = field(default_factory=dict)


@dataclass
class StarMakerConfig:
    """Root configuration."""

    project: ProjectConfig = field(default_factory=ProjectConfig)
    author: AuthorConfig = field(default_factory=AuthorConfig)
    promotion: PromotionConfig = field(default_factory=PromotionConfig)


def find_config(start_dir: Path | None = None) -> Path | None:
    """Find starmaker.yaml in current or parent directories."""
    current = start_dir or Path.cwd()
    for directory in [current, *current.parents]:
        config_path = directory / "starmaker.yaml"
        if config_path.exists():
            return config_path
    return None


def _is_valid_repo_url(url: str) -> bool:
    """Return True if ``url`` looks like a usable repository URL.

    Accepts http(s) URLs that have a network location, and ``git@host:path``
    style SSH URLs. Intentionally lenient so self-hosted GitLab/Gitea/etc.
    instances are accepted, not just GitHub.
    """
    if url.startswith("git@") and ":" in url:
        return True
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _validate_config(config: StarMakerConfig) -> None:
    """Validate a config loaded from a file, raising ``ConfigError`` on problems.

    Only the fields a user is expected to fill in are checked: a non-empty
    project name and, when provided, a well-formed repository URL. This is
    invoked only when a non-empty config file was actually loaded, so the
    empty default ``StarMakerConfig()`` returned when no file exists is never
    rejected.
    """
    if not config.project.name.strip():
        raise ConfigError(
            "Project name is required. Set 'project.name' in starmaker.yaml."
        )

    repo = config.project.repo.strip()
    if repo and not _is_valid_repo_url(repo):
        raise ConfigError(
            f"Invalid repository URL: {repo!r}. "
            "Expected an https URL (e.g. https://github.com/owner/name) "
            "or a git@host:owner/name SSH URL. Fix 'project.repo' in starmaker.yaml."
        )


def load_config(config_path: Path | None = None) -> StarMakerConfig:
    """Load configuration from starmaker.yaml.

    Returns an empty default ``StarMakerConfig`` when no config file is found.
    When a config file is present, its contents are validated and a
    user-facing ``ConfigError`` is raised on invalid input (e.g. a missing
    project name or a malformed repository URL).
    """
    if config_path is None:
        config_path = find_config()

    if config_path is None or not config_path.exists():
        return StarMakerConfig()

    with open(config_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    config = StarMakerConfig()

    # An empty/whitespace-only file is treated like "no config": no validation.
    if not raw:
        return config

    if not isinstance(raw, dict):
        raise ConfigError(
            "Invalid starmaker.yaml: expected a top-level mapping "
            "(project/author/promotion sections)."
        )

    # Project
    proj = raw.get("project") or {}
    if not isinstance(proj, dict):
        raise ConfigError("Invalid starmaker.yaml: 'project' must be a mapping.")
    config.project = ProjectConfig(
        name=str(proj.get("name", "")),
        repo=str(proj.get("repo", "")),
        tagline=str(proj.get("tagline", "")),
        description=str(proj.get("description", "")).strip(),
        website=str(proj.get("website", "")),
        competitors=proj.get("competitors") or [],
        tags=proj.get("tags") or [],
        highlights=proj.get("highlights") or [],
        tech_stack=proj.get("tech_stack") or [],
    )

    # Author
    auth = raw.get("author") or {}
    if not isinstance(auth, dict):
        raise ConfigError("Invalid starmaker.yaml: 'author' must be a mapping.")
    config.author = AuthorConfig(
        name=str(auth.get("name", "")),
        github=str(auth.get("github", "")),
        twitter=str(auth.get("twitter", "")),
        website=str(auth.get("website", "")),
    )

    # Promotion
    promo = raw.get("promotion") or {}
    if not isinstance(promo, dict):
        raise ConfigError("Invalid starmaker.yaml: 'promotion' must be a mapping.")
    config.promotion = PromotionConfig(
        platforms=promo.get("platforms") or ["reddit", "hackernews", "devto", "twitter", "discord"],
        reddit=promo.get("reddit") or {},
        awesome_lists=promo.get("awesome_lists") or [],
        comparison=promo.get("comparison") or {},
    )

    _validate_config(config)

    return config


def detect_local_repo() -> dict[str, str]:
    """Detect git repo info from the current directory.

    Returns a dict with ``repo``, ``owner`` and ``name`` keys when an ``origin``
    remote is found, or an empty dict otherwise. If git is unavailable or times
    out, the failure is logged as a warning and an empty dict is returned.
    """
    info: dict[str, str] = {}
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Convert SSH to HTTPS URL
            if url.startswith("git@github.com:"):
                url = url.replace("git@github.com:", "https://github.com/")
            if url.endswith(".git"):
                url = url[:-4]
            info["repo"] = url

            # Extract owner/name
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                info["owner"] = parts[-2]
                info["name"] = parts[-1]
    except subprocess.TimeoutExpired:
        logger.warning("git remote lookup timed out; skipping repo auto-detection.")
    except FileNotFoundError:
        logger.warning("git executable not found; skipping repo auto-detection.")

    return info
