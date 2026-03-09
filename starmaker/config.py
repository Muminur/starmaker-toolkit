"""Configuration loader for StarMaker."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProjectConfig:
    """Project configuration loaded from starmaker.yaml."""

    name: str = ""
    repo: str = ""
    tagline: str = ""
    description: str = ""
    website: str = ""
    competitors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    tech_stack: list[str] = field(default_factory=list)


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


def load_config(config_path: Path | None = None) -> StarMakerConfig:
    """Load configuration from starmaker.yaml."""
    if config_path is None:
        config_path = find_config()

    if config_path is None or not config_path.exists():
        return StarMakerConfig()

    with open(config_path) as f:
        raw = yaml.safe_load(f) or {}

    config = StarMakerConfig()

    # Project
    proj = raw.get("project", {})
    config.project = ProjectConfig(
        name=proj.get("name", ""),
        repo=proj.get("repo", ""),
        tagline=proj.get("tagline", ""),
        description=proj.get("description", "").strip(),
        website=proj.get("website", ""),
        competitors=proj.get("competitors", []),
        tags=proj.get("tags", []),
        highlights=proj.get("highlights", []),
        tech_stack=proj.get("tech_stack", []),
    )

    # Author
    auth = raw.get("author", {})
    config.author = AuthorConfig(
        name=auth.get("name", ""),
        github=auth.get("github", ""),
        twitter=auth.get("twitter", ""),
        website=auth.get("website", ""),
    )

    # Promotion
    promo = raw.get("promotion", {})
    config.promotion = PromotionConfig(
        platforms=promo.get("platforms", ["reddit", "hackernews", "devto", "twitter", "discord"]),
        reddit=promo.get("reddit", {}),
        awesome_lists=promo.get("awesome_lists", []),
        comparison=promo.get("comparison", {}),
    )

    return config


def detect_local_repo() -> dict[str, str]:
    """Detect git repo info from the current directory."""
    info = {}
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
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return info
