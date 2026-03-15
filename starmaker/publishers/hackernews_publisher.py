"""Hacker News publisher.

HN does not have an official posting API. This publisher opens the
submission form in the user's browser with pre-filled fields.
"""

from __future__ import annotations

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
        """Open HN submit page and fill form fields."""
        url = kwargs.get("url", "")

        submit_url = "https://news.ycombinator.com/submitlink"

        # HN form fields: title, url, text
        fields = {"input[name='title']": title[:80]}
        if url:
            fields["input[name='url']"] = url
        else:
            fields["textarea[name='text']"] = body[:2000]

        try:
            from starmaker.publishers._camoufox_open import open_in_camoufox
            from starmaker.utils.console import console

            console.print("[dim]Opening Hacker News in Camoufox...[/dim]")
            open_in_camoufox(submit_url, platform="hackernews", fields=fields)
            console.print("[green]Hacker News browser session complete.[/green]")

            return PostResult(
                platform="Hacker News",
                success=True,
                url=submit_url,
                message="Opened HN submission page in Camoufox. Log in and click Submit.",
            )
        except ImportError:
            import webbrowser
            webbrowser.open(submit_url)
            return PostResult(
                platform="Hacker News",
                success=True,
                url=submit_url,
                message="Opened HN submission page in default browser (Camoufox not installed).",
            )
        except Exception as e:
            return PostResult(
                platform="Hacker News",
                success=False,
                error=f"Could not open browser: {e}",
            )
