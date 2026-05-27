"""Discord publisher using webhooks.

Discord webhooks allow posting messages to channels without a bot.
Create a webhook: Server Settings > Integrations > Webhooks > New Webhook
"""

from __future__ import annotations

import requests

from starmaker.publishers.base import BasePublisher, PostResult

# Valid Discord webhook URL prefixes (discord.com and the legacy discordapp.com).
_WEBHOOK_PREFIXES = (
    "https://discord.com/api/webhooks/",
    "https://discordapp.com/api/webhooks/",
    "https://canary.discord.com/api/webhooks/",
    "https://ptb.discord.com/api/webhooks/",
)


class DiscordPublisher(BasePublisher):
    """Post messages to Discord channels via webhooks.

    Each webhook URL corresponds to one channel.
    Create webhooks at: Server Settings > Integrations > Webhooks
    """

    platform_name = "Discord"
    requires_keys = ("discord_webhook_urls",)  # Comma-separated webhook URLs

    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        """Return True when at least one webhook URL is configured (non-empty)."""
        urls = credentials.get("discord_webhook_urls", "")
        return bool(urls.strip())

    @staticmethod
    def _is_valid_webhook(url: str) -> bool:
        """Return True if ``url`` looks like a Discord webhook endpoint."""
        return url.startswith(_WEBHOOK_PREFIXES)

    def _parse_webhook_urls(self, credentials: dict[str, str]) -> list[str]:
        """Parse the comma-separated ``discord_webhook_urls`` credential.

        Args:
            credentials: Mapping containing ``discord_webhook_urls``.

        Returns:
            A list of individual, whitespace-stripped webhook URLs.
        """
        raw = credentials.get("discord_webhook_urls", "")
        return [url.strip() for url in raw.split(",") if url.strip()]

    def publish(self, title: str, body: str, credentials: dict[str, str], **kwargs) -> PostResult:
        """Post a message to one or more Discord webhooks.

        Partial-failure policy: every configured webhook is attempted; a
        malformed URL is reported and skipped without aborting the others.
        The returned ``message`` always reports how many of the configured
        webhooks succeeded (``N/M``). ``success`` is True only when *every*
        configured webhook succeeded (all-or-nothing), preserving the
        established public contract.

        Args:
            title: Used as the message content only when ``body`` is empty.
            body: Message content (truncated to Discord's 2000-char limit).
            credentials: Must contain ``discord_webhook_urls``.
            **kwargs: Supports ``username`` (webhook display name).

        Returns:
            A :class:`PostResult` describing the per-webhook outcome.
        """
        webhook_urls = self._parse_webhook_urls(credentials)

        if not webhook_urls:
            return PostResult(
                platform="Discord",
                success=False,
                error="No Discord webhook URLs configured.",
            )

        total = len(webhook_urls)
        successes: list[str] = []
        failures: list[str] = []

        # Discord webhook content limit is 2000 chars.
        content = (body[:2000] if body else title)
        payload = {
            "content": content,
            "username": kwargs.get("username", "StarMaker"),
        }

        for i, webhook_url in enumerate(webhook_urls, start=1):
            if not self._is_valid_webhook(webhook_url):
                failures.append(f"Webhook {i}: invalid URL (not a Discord webhook endpoint)")
                continue

            try:
                resp = requests.post(webhook_url, json=payload, timeout=10)
            except requests.RequestException as e:
                failures.append(f"Webhook {i}: request error - {e}")
                continue

            if resp.status_code in (200, 204):
                successes.append(f"Webhook {i}: posted successfully")
            else:
                failures.append(f"Webhook {i}: HTTP {resp.status_code}")

        success_count = len(successes)
        all_success = success_count == total
        detail = "; ".join(successes + failures)

        return PostResult(
            platform="Discord",
            success=all_success,
            message=f"Posted to {success_count}/{total} webhook(s). {detail}",
            error="" if all_success else "; ".join(failures),
        )
