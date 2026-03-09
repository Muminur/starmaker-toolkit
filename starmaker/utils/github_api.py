"""GitHub API and local git analysis utilities."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from typing import Any

import requests


@dataclass
class RepoInfo:
    """Aggregated repository information."""

    name: str = ""
    full_name: str = ""
    description: str = ""
    url: str = ""
    homepage: str = ""
    language: str = ""
    languages: dict[str, int] = field(default_factory=dict)
    license: str = ""
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    topics: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    has_readme: bool = False
    has_license: bool = False
    has_contributing: bool = False
    has_changelog: bool = False
    has_ci: bool = False
    has_releases: bool = False
    release_count: int = 0
    latest_release: str = ""
    default_branch: str = "main"
    commit_count: int = 0
    contributor_count: int = 0
    has_description: bool = False
    has_homepage: bool = False
    has_topics: bool = False


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Extract owner and repo name from a GitHub URL."""
    patterns = [
        r"github\.com[:/]([^/]+)/([^/.]+)",
        r"^([^/]+)/([^/]+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
    return None


def fetch_repo_info(repo_url: str) -> RepoInfo:
    """Fetch repository info from GitHub API."""
    parsed = parse_github_url(repo_url)
    if not parsed:
        raise ValueError(f"Could not parse GitHub URL: {repo_url}")

    owner, repo = parsed
    info = RepoInfo()

    # Basic repo info
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers={"Accept": "application/vnd.github.v3+json"},
        timeout=10,
    )
    if resp.status_code == 200:
        data = resp.json()
        info.name = data.get("name", "")
        info.full_name = data.get("full_name", "")
        info.description = data.get("description", "") or ""
        info.url = data.get("html_url", "")
        info.homepage = data.get("homepage", "") or ""
        info.language = data.get("language", "") or ""
        info.license = (data.get("license") or {}).get("spdx_id", "")
        info.stars = data.get("stargazers_count", 0)
        info.forks = data.get("forks_count", 0)
        info.watchers = data.get("subscribers_count", 0)
        info.open_issues = data.get("open_issues_count", 0)
        info.topics = data.get("topics", [])
        info.created_at = data.get("created_at", "")
        info.updated_at = data.get("updated_at", "")
        info.default_branch = data.get("default_branch", "main")
        info.has_description = bool(info.description)
        info.has_homepage = bool(info.homepage)
        info.has_topics = len(info.topics) > 0
    elif resp.status_code == 404:
        raise ValueError(f"Repository not found: {owner}/{repo}")
    else:
        raise ConnectionError(f"GitHub API error: {resp.status_code}")

    # Languages
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/languages",
        headers={"Accept": "application/vnd.github.v3+json"},
        timeout=10,
    )
    if resp.status_code == 200:
        info.languages = resp.json()

    # Check for key files
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/contents/",
        headers={"Accept": "application/vnd.github.v3+json"},
        timeout=10,
    )
    if resp.status_code == 200:
        files = {item["name"].lower() for item in resp.json() if isinstance(item, dict)}
        info.has_readme = any(f.startswith("readme") for f in files)
        info.has_license = any(f.startswith("license") or f.startswith("licence") for f in files)
        info.has_contributing = any(f.startswith("contributing") for f in files)
        info.has_changelog = any(f.startswith("changelog") for f in files)

    # Check for CI
    for ci_path in [".github/workflows", ".circleci", ".travis.yml"]:
        resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{ci_path}",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10,
        )
        if resp.status_code == 200:
            info.has_ci = True
            break

    # Releases
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/releases",
        headers={"Accept": "application/vnd.github.v3+json"},
        timeout=10,
    )
    if resp.status_code == 200:
        releases = resp.json()
        info.release_count = len(releases)
        info.has_releases = len(releases) > 0
        if releases:
            info.latest_release = releases[0].get("tag_name", "")

    # Contributors (first page)
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/contributors",
        params={"per_page": 1, "anon": "true"},
        headers={"Accept": "application/vnd.github.v3+json"},
        timeout=10,
    )
    if resp.status_code == 200:
        # Check Link header for total count
        link = resp.headers.get("Link", "")
        if 'rel="last"' in link:
            import re as _re
            match = _re.search(r'page=(\d+)>; rel="last"', link)
            if match:
                info.contributor_count = int(match.group(1))
        else:
            info.contributor_count = len(resp.json())

    return info


def get_local_repo_info() -> dict[str, Any]:
    """Gather info from the local git repository."""
    info: dict[str, Any] = {}

    try:
        # Remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            info["remote_url"] = result.stdout.strip()

        # Commit count
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            info["commit_count"] = int(result.stdout.strip())

        # Last commit date
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            info["last_commit"] = result.stdout.strip()

        # Branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip()

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return info
