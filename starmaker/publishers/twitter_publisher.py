"""Twitter/X publisher.

Twitter API v2 requires paid access ($100/mo Basic plan).
This publisher supports two modes:
1. If API keys are provided: posts via official API v2
2. If no keys: opens Twitter intent URL in browser (free)
"""

from __future__ import annotations

import urllib.parse

import requests

from starmaker.publishers.base import BasePublisher, PostResult


class TwitterPublisher(BasePublisher):
    """Publish tweets via Twitter API v2 or browser intent.

    API keys from: https://developer.twitter.com/en/portal/dashboard
    Browser intent: works without any API keys (free).
    """

    platform_name = "Twitter/X"
    requires_keys = []  # Optional — falls back to browser intent

    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        # Always valid — browser intent works without keys
        return True

    def _has_api_keys(self, credentials: dict[str, str]) -> bool:
        """Check if Twitter API keys are configured."""
        return all(
            credentials.get(k)
            for k in ["twitter_bearer_token", "twitter_api_key", "twitter_api_secret",
                       "twitter_access_token", "twitter_access_secret"]
        )

    def _post_via_api(self, text: str, credentials: dict[str, str]) -> PostResult:
        """Post via Twitter API v2 (requires paid plan)."""
        # OAuth 1.0a User Context
        from requests_oauthlib import OAuth1

        auth = OAuth1(
            credentials["twitter_api_key"],
            credentials["twitter_api_secret"],
            credentials["twitter_access_token"],
            credentials["twitter_access_secret"],
        )

        resp = requests.post(
            "https://api.twitter.com/2/tweets",
            json={"text": text[:280]},
            auth=auth,
            timeout=10,
        )

        if resp.status_code in (200, 201):
            data = resp.json()
            tweet_id = data.get("data", {}).get("id", "")
            username = credentials.get("twitter_username", "user")
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
            return PostResult(
                platform="Twitter/X",
                success=True,
                url=tweet_url,
                message="Tweet posted via API",
            )

        return PostResult(
            platform="Twitter/X",
            success=False,
            error=f"HTTP {resp.status_code}: {resp.text[:200]}",
        )

    def _post_via_intent(self, text: str) -> PostResult:
        """Open Twitter web intent in default browser (free, no API keys needed)."""
        import webbrowser
        intent_url = "https://twitter.com/intent/tweet?" + urllib.parse.urlencode({"text": text[:280]})

        try:
            webbrowser.open(intent_url)
            return PostResult(
                platform="Twitter/X",
                success=True,
                url=intent_url,
                message="Opened Twitter compose window in your browser. Review and click Tweet.",
            )
        except Exception as e:
            return PostResult(
                platform="Twitter/X",
                success=False,
                error=f"Could not open browser: {e}",
            )

    def publish(self, title: str, body: str, credentials: dict[str, str], **kwargs) -> PostResult:
        """Post a tweet. Uses API if keys available, otherwise browser intent."""
        # For Twitter, body IS the tweet text. Title is ignored.
        tweet_text = body[:280] if body else title[:280]

        if self._has_api_keys(credentials):
            try:
                return self._post_via_api(tweet_text, credentials)
            except ImportError:
                return PostResult(
                    platform="Twitter/X",
                    success=False,
                    error="Twitter API requires 'requests-oauthlib'. Install with: pip install requests-oauthlib",
                )
        else:
            return self._post_via_intent(tweet_text)
