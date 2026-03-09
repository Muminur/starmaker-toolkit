"""Hacker News publisher.

HN does not have an official posting API. This publisher opens the
submission form in the user's browser with pre-filled fields.
"""

from __future__ import annotations

import urllib.parse
import webbrowser

from starmaker.publishers.base import BasePublisher, PostResult


class HackerNewsPublisher(BasePublisher):
    """Open HN submission page in browser with pre-filled title/URL.

    HN has no official posting API, so we open the browser for the user.
    """

    platform_name = "Hacker News"
    requires_keys = []  # No API keys needed — browser-based

    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        return True  # No credentials needed

    def publish(self, title: str, body: str, credentials: dict[str, str], **kwargs) -> PostResult:
        """Open HN submit page in default browser."""
        url = kwargs.get("url", "")

        params = {"title": title[:80]}
        if url:
            params["url"] = url
        else:
            params["text"] = body[:2000]

        submit_url = "https://news.ycombinator.com/submitlink?" + urllib.parse.urlencode(params)

        try:
            webbrowser.open(submit_url)
            return PostResult(
                platform="Hacker News",
                success=True,
                url=submit_url,
                message="Opened HN submission page in your browser. Log in and click Submit.",
            )
        except Exception as e:
            return PostResult(
                platform="Hacker News",
                success=False,
                error=f"Could not open browser: {e}",
            )
