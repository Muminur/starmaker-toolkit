"""GitHub API and local git analysis utilities.

This module provides helpers to:

* parse GitHub URLs into ``(owner, repo)`` tuples;
* fetch aggregated repository metadata from the GitHub REST API using a
  shared :class:`requests.Session` configured with automatic retries and
  rate-limit awareness;
* gather information from a local git checkout via the ``git`` CLI.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

#: GitHub REST API base URL.
_API_BASE = "https://api.github.com"

#: Headers sent with every GitHub API request.
_DEFAULT_HEADERS = {"Accept": "application/vnd.github.v3+json"}

#: Default per-request timeout (seconds).
_TIMEOUT = 10

#: Pattern used to extract the total page count from a ``Link`` header.
_LINK_LAST_RE = re.compile(r'[?&]page=(\d+)>;\s*rel="last"')


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


def _build_session() -> requests.Session:
    """Create a :class:`requests.Session` with retry/backoff on transient errors.

    The session retries on connection errors and transient server-side
    failures (HTTP 502/503/504) using exponential backoff. GitHub's own
    rate-limit responses (403/429) are *not* auto-retried here; they are
    surfaced explicitly to the caller so they can be reported clearly.

    Returns:
        A configured session shared across all requests in this module.
    """
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=(502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update(_DEFAULT_HEADERS)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


#: Module-level session reused across requests (connection pooling + retries).
_session = _build_session()


def _is_rate_limited(resp: requests.Response) -> bool:
    """Return ``True`` if *resp* indicates the GitHub rate limit was exhausted.

    GitHub signals an exhausted primary rate limit with HTTP 403 (or 429) and
    an ``X-RateLimit-Remaining: 0`` header.
    """
    if resp.status_code not in (403, 429):
        return False
    remaining = resp.headers.get("X-RateLimit-Remaining")
    if resp.status_code == 429:
        return True
    return remaining == "0"


def _raise_for_api_error(resp: requests.Response, owner: str, repo: str) -> None:
    """Raise a descriptive error for a non-success GitHub API response.

    Distinguishes the common failure modes so callers (and users) get an
    actionable message instead of a bare status code:

    * **rate limit** (403/429 with ``X-RateLimit-Remaining: 0``) -> includes
      the ``Retry-After`` hint when present;
    * **auth** (401, or 403 without rate-limit exhaustion) -> bad/missing token;
    * **not found** (404) -> repo missing or private;
    * anything else -> generic :class:`ConnectionError` with the status code.

    Args:
        resp: The HTTP response to inspect.
        owner: Repository owner, used in the message.
        repo: Repository name, used in the message.

    Raises:
        ValueError: For 404 (not found).
        ConnectionError: For auth, rate-limit, and other unexpected statuses.
    """
    status = resp.status_code

    if _is_rate_limited(resp):
        retry_after = resp.headers.get("Retry-After")
        hint = f" Retry after {retry_after}s." if retry_after else ""
        raise ConnectionError(
            "GitHub API rate limit exceeded. Set a GITHUB_TOKEN to raise the "
            f"limit, or wait before retrying.{hint}"
        )

    if status == 401 or status == 403:
        raise ConnectionError(
            "GitHub API authentication failed "
            f"(HTTP {status}). Check that your GITHUB_TOKEN is valid and has "
            "the required scopes."
        )

    if status == 404:
        raise ValueError(f"Repository not found: {owner}/{repo}")

    raise ConnectionError(f"GitHub API error (HTTP {status}) for {owner}/{repo}")


def _get(url: str, **kwargs: Any) -> requests.Response:
    """Perform a GET request through the shared session.

    Args:
        url: Fully-qualified URL to fetch.
        **kwargs: Extra arguments forwarded to :meth:`requests.Session.get`
            (e.g. ``params``). A default ``timeout`` is applied if not given.

    Returns:
        The HTTP response.
    """
    kwargs.setdefault("timeout", _TIMEOUT)
    return _session.get(url, **kwargs)


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Extract owner and repo name from a GitHub URL.

    Accepts full URLs (``https://github.com/owner/repo``), SSH-style
    (``git@github.com:owner/repo.git``), and the short ``owner/repo`` form.

    Args:
        url: The string to parse.

    Returns:
        A ``(owner, repo)`` tuple, or ``None`` if *url* does not match.
    """
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
    """Fetch repository info from the GitHub API.

    Args:
        repo_url: A GitHub URL or ``owner/repo`` shorthand.

    Returns:
        A populated :class:`RepoInfo`.

    Raises:
        ValueError: If *repo_url* cannot be parsed or the repo is not found.
        ConnectionError: On auth failure, rate limiting, or other API errors.
    """
    parsed = parse_github_url(repo_url)
    if not parsed:
        raise ValueError(f"Could not parse GitHub URL: {repo_url}")

    owner, repo = parsed
    info = RepoInfo()
    base = f"{_API_BASE}/repos/{owner}/{repo}"

    # Basic repo info — this is the authoritative call; surface any error.
    resp = _get(base)
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
    else:
        _raise_for_api_error(resp, owner, repo)

    # Languages
    resp = _get(f"{base}/languages")
    if resp.status_code == 200:
        info.languages = resp.json()

    # Check for key files
    resp = _get(f"{base}/contents/")
    if resp.status_code == 200:
        files = {item["name"].lower() for item in resp.json() if isinstance(item, dict)}
        info.has_readme = any(f.startswith("readme") for f in files)
        info.has_license = any(f.startswith("license") or f.startswith("licence") for f in files)
        info.has_contributing = any(f.startswith("contributing") for f in files)
        info.has_changelog = any(f.startswith("changelog") for f in files)

    # Check for CI
    for ci_path in [".github/workflows", ".circleci", ".travis.yml"]:
        resp = _get(f"{base}/contents/{ci_path}")
        if resp.status_code == 200:
            info.has_ci = True
            break

    # Releases
    resp = _get(f"{base}/releases")
    if resp.status_code == 200:
        releases = resp.json()
        info.release_count = len(releases)
        info.has_releases = len(releases) > 0
        if releases:
            info.latest_release = releases[0].get("tag_name", "")

    # Contributors (first page only; total inferred from Link header)
    resp = _get(
        f"{base}/contributors",
        params={"per_page": 1, "anon": "true"},
    )
    if resp.status_code == 200:
        link = resp.headers.get("Link", "")
        match = _LINK_LAST_RE.search(link)
        if match:
            info.contributor_count = int(match.group(1))
        else:
            info.contributor_count = len(resp.json())

    return info


def get_local_repo_info() -> dict[str, Any]:
    """Gather info from the local git repository.

    Returns:
        A dict with any of ``remote_url``, ``commit_count``, ``last_commit``,
        and ``branch`` that could be determined. Returns an empty/partial dict
        if git is unavailable or a command times out.
    """
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
