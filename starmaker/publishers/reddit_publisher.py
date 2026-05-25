"""Reddit publisher using official OAuth2 API."""

from __future__ import annotations

import re

import requests

from starmaker import __version__
from starmaker.publishers.base import BasePublisher, PostResult

# Reddit subreddit names: 3-21 chars, letters/digits/underscores only.
_SUBREDDIT_RE = re.compile(r"^[A-Za-z0-9_]{3,21}$")


class RedditPublisher(BasePublisher):
    """Publish posts to Reddit via official API.

    Requires a Reddit app (script type) created at https://www.reddit.com/prefs/apps/
    """

    platform_name = "Reddit"
    requires_keys = (
        "reddit_client_id",
        "reddit_client_secret",
        "reddit_username",
        "reddit_password",
    )

    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        """Return True when all required Reddit OAuth credentials are present."""
        missing = self.get_missing_keys(credentials)
        return len(missing) == 0

    def _user_agent(self, username: str) -> str:
        """Build the API User-Agent string from the package version."""
        return f"StarMaker/{__version__} (by /u/{username})"

    def _get_access_token(self, credentials: dict[str, str]) -> str | None:
        """Obtain an OAuth2 access token using the script app password flow.

        Args:
            credentials: Reddit API credentials.

        Returns:
            The bearer access token, or None if authentication failed.
        """
        auth = (credentials["reddit_client_id"], credentials["reddit_client_secret"])
        data = {
            "grant_type": "password",
            "username": credentials["reddit_username"],
            "password": credentials["reddit_password"],
        }
        headers = {"User-Agent": self._user_agent(credentials["reddit_username"])}

        resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth,
            data=data,
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            token_data = resp.json()
            return token_data.get("access_token")
        return None

    def publish(self, title: str, body: str, credentials: dict[str, str], **kwargs) -> PostResult:
        """Post a self (text) submission to a subreddit.

        Args:
            title: Submission title (truncated to 300 chars by Reddit).
            body: Submission body markdown.
            credentials: Reddit API credentials.
            **kwargs: Supports ``subreddit`` (name without the ``r/`` prefix).

        Returns:
            A :class:`PostResult` describing the outcome.
        """
        subreddit = kwargs.get("subreddit", "test")

        if not _SUBREDDIT_RE.match(subreddit):
            return PostResult(
                platform=f"Reddit r/{subreddit}",
                success=False,
                error=(
                    f"Invalid subreddit name '{subreddit}'. Names must be 3-21 "
                    "characters using only letters, digits, and underscores."
                ),
            )

        token = self._get_access_token(credentials)
        if not token:
            return PostResult(
                platform=f"Reddit r/{subreddit}",
                success=False,
                error="Failed to authenticate. Check your Reddit API credentials.",
            )

        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": self._user_agent(credentials["reddit_username"]),
        }

        data = {
            "sr": subreddit,
            "kind": "self",
            "title": title[:300],
            "text": body,
            "resubmit": True,
        }

        resp = requests.post(
            "https://oauth.reddit.com/api/submit",
            headers=headers,
            data=data,
            timeout=15,
        )

        if resp.status_code == 200:
            result = resp.json()
            # Reddit returns nested json
            if "json" in result and "data" in result["json"]:
                post_url = result["json"]["data"].get("url", "")
                return PostResult(
                    platform=f"Reddit r/{subreddit}",
                    success=True,
                    url=post_url,
                    message=f"Posted to r/{subreddit}",
                )
            # Check for errors in response
            errors = result.get("json", {}).get("errors", [])
            if errors:
                error_msg = "; ".join(str(e) for e in errors)
                return PostResult(
                    platform=f"Reddit r/{subreddit}",
                    success=False,
                    error=f"Reddit API error: {error_msg}",
                )
            return PostResult(
                platform=f"Reddit r/{subreddit}",
                success=True,
                message=f"Posted to r/{subreddit} (URL not returned)",
            )

        return PostResult(
            platform=f"Reddit r/{subreddit}",
            success=False,
            error=f"HTTP {resp.status_code}: {resp.text[:200]}",
        )
