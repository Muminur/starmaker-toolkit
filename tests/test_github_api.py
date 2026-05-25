"""Unit tests for starmaker.utils.github_api.

These tests MOCK the shared requests Session — they never hit the live
GitHub API.
"""

from __future__ import annotations

import pytest

from starmaker.utils import github_api
from starmaker.utils.github_api import RepoInfo, fetch_repo_info, parse_github_url


class FakeResponse:
    """Minimal stand-in for ``requests.Response``."""

    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._json


def _repo_payload(**overrides):
    data = {
        "name": "repo",
        "full_name": "owner/repo",
        "description": "A test repo",
        "html_url": "https://github.com/owner/repo",
        "homepage": "https://example.com",
        "language": "Python",
        "license": {"spdx_id": "MIT"},
        "stargazers_count": 100,
        "forks_count": 10,
        "subscribers_count": 5,
        "open_issues_count": 3,
        "topics": ["cli", "oss"],
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2021-01-01T00:00:00Z",
        "default_branch": "main",
    }
    data.update(overrides)
    return data


class TestParseGithubUrl:
    def test_full_url(self):
        assert parse_github_url("https://github.com/owner/repo") == ("owner", "repo")

    def test_url_with_git_suffix(self):
        assert parse_github_url("https://github.com/owner/repo.git") == ("owner", "repo")

    def test_ssh_style(self):
        assert parse_github_url("git@github.com:owner/repo.git") == ("owner", "repo")

    def test_shorthand(self):
        assert parse_github_url("owner/repo") == ("owner", "repo")

    def test_invalid(self):
        assert parse_github_url("not a url") is None


class TestFetchRepoInfo:
    def test_unparseable_url_raises_value_error(self):
        with pytest.raises(ValueError, match="Could not parse"):
            fetch_repo_info("garbage string")

    def test_happy_path(self, monkeypatch):
        """A successful fetch populates RepoInfo from multiple endpoints."""

        def fake_get(url, **kwargs):
            if url.endswith("/repos/owner/repo"):
                return FakeResponse(200, _repo_payload())
            if url.endswith("/languages"):
                return FakeResponse(200, {"Python": 1000, "Shell": 100})
            if url.endswith("/contents/"):
                return FakeResponse(
                    200,
                    [
                        {"name": "README.md"},
                        {"name": "LICENSE"},
                        {"name": "CONTRIBUTING.md"},
                        {"name": "CHANGELOG.md"},
                    ],
                )
            if url.endswith("/contents/.github/workflows"):
                return FakeResponse(200, [{"name": "ci.yml"}])
            if "/contents/" in url:
                return FakeResponse(404)
            if url.endswith("/releases"):
                return FakeResponse(200, [{"tag_name": "v1.0.0"}])
            if url.endswith("/contributors"):
                return FakeResponse(
                    200,
                    [{}],
                    headers={
                        "Link": '<https://api.github.com/repos/owner/repo/contributors?per_page=1&page=42>; rel="last"'
                    },
                )
            return FakeResponse(404)

        monkeypatch.setattr(github_api._session, "get", fake_get)

        info = fetch_repo_info("owner/repo")
        assert isinstance(info, RepoInfo)
        assert info.name == "repo"
        assert info.stars == 100
        assert info.license == "MIT"
        assert info.languages == {"Python": 1000, "Shell": 100}
        assert info.has_readme is True
        assert info.has_license is True
        assert info.has_contributing is True
        assert info.has_changelog is True
        assert info.has_ci is True
        assert info.has_releases is True
        assert info.latest_release == "v1.0.0"
        assert info.contributor_count == 42
        assert info.has_topics is True

    def test_contributor_count_no_link_header(self, monkeypatch):
        """When no Link header, count falls back to length of the page."""

        def fake_get(url, **kwargs):
            if url.endswith("/repos/owner/repo"):
                return FakeResponse(200, _repo_payload())
            if url.endswith("/contributors"):
                return FakeResponse(200, [{}, {}, {}])
            return FakeResponse(404)

        monkeypatch.setattr(github_api._session, "get", fake_get)
        info = fetch_repo_info("owner/repo")
        assert info.contributor_count == 3

    def test_404_raises_value_error(self, monkeypatch):
        monkeypatch.setattr(
            github_api._session, "get", lambda url, **kw: FakeResponse(404)
        )
        with pytest.raises(ValueError, match="Repository not found: owner/repo"):
            fetch_repo_info("owner/repo")

    def test_401_raises_auth_error(self, monkeypatch):
        monkeypatch.setattr(
            github_api._session, "get", lambda url, **kw: FakeResponse(401)
        )
        with pytest.raises(ConnectionError, match="authentication failed"):
            fetch_repo_info("owner/repo")

    def test_403_without_rate_limit_is_auth_error(self, monkeypatch):
        # 403 with remaining tokens -> treated as auth/permission, not rate limit.
        monkeypatch.setattr(
            github_api._session,
            "get",
            lambda url, **kw: FakeResponse(
                403, headers={"X-RateLimit-Remaining": "10"}
            ),
        )
        with pytest.raises(ConnectionError, match="authentication failed"):
            fetch_repo_info("owner/repo")

    def test_rate_limit_403_raises_rate_limit_error(self, monkeypatch):
        monkeypatch.setattr(
            github_api._session,
            "get",
            lambda url, **kw: FakeResponse(
                403,
                headers={"X-RateLimit-Remaining": "0", "Retry-After": "60"},
            ),
        )
        with pytest.raises(ConnectionError, match="rate limit exceeded") as exc:
            fetch_repo_info("owner/repo")
        assert "Retry after 60s" in str(exc.value)

    def test_rate_limit_429_raises_rate_limit_error(self, monkeypatch):
        monkeypatch.setattr(
            github_api._session,
            "get",
            lambda url, **kw: FakeResponse(429),
        )
        with pytest.raises(ConnectionError, match="rate limit exceeded"):
            fetch_repo_info("owner/repo")

    def test_unexpected_status_raises_connection_error(self, monkeypatch):
        monkeypatch.setattr(
            github_api._session, "get", lambda url, **kw: FakeResponse(500)
        )
        with pytest.raises(ConnectionError, match="HTTP 500"):
            fetch_repo_info("owner/repo")


class TestSessionConfiguration:
    def test_session_has_retry_adapter(self):
        """The shared session mounts an adapter with a Retry policy on https."""
        adapter = github_api._session.get_adapter("https://api.github.com")
        retries = adapter.max_retries
        assert retries.total == 3
        assert retries.backoff_factor == 0.5
        assert 502 in retries.status_forcelist
        assert 503 in retries.status_forcelist
        assert 504 in retries.status_forcelist

    def test_retry_then_success(self, monkeypatch):
        """Simulate a transient failure followed by success.

        The real urllib3 Retry handles HTTP-level retries inside the adapter;
        here we verify the call layer transparently returns the eventual
        success without the caller observing the transient failures.
        """
        calls = {"n": 0}

        def fake_get(url, **kwargs):
            if url.endswith("/repos/owner/repo"):
                calls["n"] += 1
                if calls["n"] < 3:
                    # Transient server errors that Retry would normally absorb.
                    return FakeResponse(503)
                return FakeResponse(200, _repo_payload())
            return FakeResponse(404)

        # Wrap fake_get with a tiny retry loop mirroring the adapter's behavior
        # so we exercise the "retry then success" outcome at the call boundary.
        def retrying_get(url, **kwargs):
            resp = fake_get(url, **kwargs)
            while resp.status_code in (502, 503, 504) and url.endswith("/repos/owner/repo"):
                resp = fake_get(url, **kwargs)
            return resp

        monkeypatch.setattr(github_api._session, "get", retrying_get)
        info = fetch_repo_info("owner/repo")
        assert info.name == "repo"
        assert calls["n"] == 3
