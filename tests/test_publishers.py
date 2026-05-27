"""Unit tests for platform publishers.

These tests never make live network calls or real posts: HTTP is mocked via
``unittest.mock.patch`` and browser launches are patched out.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from starmaker import __version__
from starmaker.publishers import PUBLISHERS
from starmaker.publishers.base import BasePublisher, PostResult
from starmaker.publishers.devto_publisher import DevtoPublisher
from starmaker.publishers.discord_publisher import DiscordPublisher
from starmaker.publishers.hackernews_publisher import HackerNewsPublisher
from starmaker.publishers.reddit_publisher import RedditPublisher
from starmaker.publishers.twitter_publisher import TwitterPublisher


def _mock_response(status_code: int, json_data: dict | None = None, text: str = "") -> MagicMock:
    """Build a stand-in for a ``requests.Response``."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text
    return resp


# Publishers whose validate_credentials() requires keys (returns False when empty).
CREDENTIALED = {"reddit": RedditPublisher, "devto": DevtoPublisher, "discord": DiscordPublisher}
# Publishers that are intentionally keyless (validate_credentials() always True).
KEYLESS = {"twitter": TwitterPublisher, "hackernews": HackerNewsPublisher}


class TestBaseContract:
    def test_requires_keys_is_immutable_tuple(self):
        """The base default must be an immutable tuple, not a shared list."""
        assert isinstance(BasePublisher.requires_keys, tuple)
        assert BasePublisher.requires_keys == ()

    def test_subclasses_use_tuple_requires_keys(self):
        for pub_cls in PUBLISHERS.values():
            assert isinstance(pub_cls.requires_keys, tuple), pub_cls.__name__

    def test_no_shared_mutable_state_between_instances(self):
        """get_missing_keys must not mutate any shared class attribute."""
        a = RedditPublisher()
        b = RedditPublisher()
        a.get_missing_keys({})
        assert list(a.requires_keys) == list(b.requires_keys)

    @pytest.mark.parametrize("name,pub_cls", PUBLISHERS.items())
    def test_registry_classes_are_publishers(self, name, pub_cls):
        assert issubclass(pub_cls, BasePublisher)
        assert pub_cls().platform_name


class TestCredentialedPublishers:
    @pytest.mark.parametrize("name,pub_cls", CREDENTIALED.items())
    def test_validate_false_with_empty_credentials(self, name, pub_cls):
        assert pub_cls().validate_credentials({}) is False

    @pytest.mark.parametrize("name,pub_cls", CREDENTIALED.items())
    def test_get_missing_keys_lists_required(self, name, pub_cls):
        missing = pub_cls().get_missing_keys({})
        assert set(missing) == set(pub_cls.requires_keys)


class TestKeylessPublishers:
    @pytest.mark.parametrize("name,pub_cls", KEYLESS.items())
    def test_validate_true_without_credentials(self, name, pub_cls):
        assert pub_cls().validate_credentials({}) is True

    @pytest.mark.parametrize("name,pub_cls", KEYLESS.items())
    def test_no_required_keys(self, name, pub_cls):
        assert pub_cls.requires_keys == ()
        assert pub_cls().get_missing_keys({}) == []


class TestReddit:
    CREDS = {
        "reddit_client_id": "id",
        "reddit_client_secret": "secret",
        "reddit_username": "tester",
        "reddit_password": "pw",
    }

    def test_user_agent_uses_package_version(self):
        ua = RedditPublisher()._user_agent("tester")
        assert ua == f"StarMaker/{__version__} (by /u/tester)"
        assert "0.1.0" not in ua

    def test_invalid_subreddit_rejected_before_network(self):
        with patch("starmaker.publishers.reddit_publisher.requests.post") as mock_post:
            result = RedditPublisher().publish("t", "b", self.CREDS, subreddit="a")  # too short
        assert isinstance(result, PostResult)
        assert result.success is False
        assert "Invalid subreddit" in result.error
        mock_post.assert_not_called()

    def test_successful_publish(self):
        token_resp = _mock_response(200, {"access_token": "tok"})
        submit_resp = _mock_response(
            200, {"json": {"data": {"url": "https://reddit.com/r/test/x"}}}
        )
        with patch(
            "starmaker.publishers.reddit_publisher.requests.post",
            side_effect=[token_resp, submit_resp],
        ):
            result = RedditPublisher().publish("Title", "Body", self.CREDS, subreddit="test")
        assert result.success is True
        assert result.url == "https://reddit.com/r/test/x"

    def test_auth_failure_returns_error_result(self):
        token_resp = _mock_response(401, {}, text="unauthorized")
        with patch(
            "starmaker.publishers.reddit_publisher.requests.post",
            return_value=token_resp,
        ):
            result = RedditPublisher().publish("Title", "Body", self.CREDS, subreddit="test")
        assert result.success is False
        assert "authenticate" in result.error.lower()


class TestDevto:
    def test_successful_draft(self):
        resp = _mock_response(201, {"url": "https://dev.to/x/article"})
        with patch("starmaker.publishers.devto_publisher.requests.post", return_value=resp):
            result = DevtoPublisher().publish("T", "B", {"devto_api_key": "k"}, tags=["a", "b"])
        assert result.success is True
        assert result.url == "https://dev.to/x/article"

    def test_http_error(self):
        resp = _mock_response(422, {}, text="bad")
        with patch("starmaker.publishers.devto_publisher.requests.post", return_value=resp):
            result = DevtoPublisher().publish("T", "B", {"devto_api_key": "k"})
        assert result.success is False
        assert "422" in result.error


class TestDiscord:
    GOOD = "https://discord.com/api/webhooks/123/abc"
    GOOD2 = "https://discord.com/api/webhooks/456/def"
    BAD = "https://evil.example.com/api/webhooks/1/x"

    def test_invalid_webhook_skipped_and_reported(self):
        creds = {"discord_webhook_urls": self.BAD}
        with patch("starmaker.publishers.discord_publisher.requests.post") as mock_post:
            result = DiscordPublisher().publish("T", "B", creds)
        mock_post.assert_not_called()
        assert result.success is False
        assert "invalid URL" in result.error
        assert "0/1" in result.message

    def test_all_success(self):
        creds = {"discord_webhook_urls": f"{self.GOOD}, {self.GOOD2}"}
        with patch(
            "starmaker.publishers.discord_publisher.requests.post",
            return_value=_mock_response(204),
        ):
            result = DiscordPublisher().publish("T", "B", creds)
        assert result.success is True
        assert "2/2" in result.message

    def test_partial_failure_reports_count(self):
        creds = {"discord_webhook_urls": f"{self.GOOD}, {self.GOOD2}"}
        with patch(
            "starmaker.publishers.discord_publisher.requests.post",
            side_effect=[_mock_response(204), _mock_response(500)],
        ):
            result = DiscordPublisher().publish("T", "B", creds)
        assert result.success is False  # all-or-nothing preserved
        assert "1/2" in result.message
        assert "500" in result.error

    def test_no_urls_configured(self):
        result = DiscordPublisher().publish("T", "B", {"discord_webhook_urls": "  "})
        assert result.success is False
        assert "No Discord webhook" in result.error


class TestTwitter:
    def test_browser_intent_fallback(self):
        with patch("webbrowser.open", return_value=True) as mock_open:
            result = TwitterPublisher().publish("Title", "Tweet body", {})
        mock_open.assert_called_once()
        assert result.success is True
        assert "intent/tweet" in result.url

    def test_browser_open_failure(self):
        with patch("webbrowser.open", side_effect=OSError("no display")):
            result = TwitterPublisher().publish("Title", "Tweet body", {})
        assert result.success is False
        assert "OSError" in result.error


class TestHackerNews:
    def test_falls_back_to_default_browser_without_camoufox(self):
        # Force the camoufox import inside publish() to fail -> ImportError branch.
        with patch.dict(
            "sys.modules", {"starmaker.publishers._camoufox_open": None}
        ), patch("webbrowser.open", return_value=True) as mock_open:
            result = HackerNewsPublisher().publish("Title", "Body", {}, url="https://x.io")
        mock_open.assert_called_once()
        assert result.success is True
        assert result.url.endswith("submitlink")
        # Confirm the ImportError (fallback) branch was taken, not the Camoufox path.
        assert "default browser" in result.message
        assert "Camoufox not installed" in result.message
