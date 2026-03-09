"""Discord publisher using webhooks.

Discord webhooks allow posting messages to channels without a bot.
Create a webhook: Server Settings > Integrations > Webhooks > New Webhook
"""

from __future__ import annotations

import requests

from starmaker.publishers.base import BasePublisher, PostResult


class DiscordPublisher(BasePublisher):
    """Post messages to Discord channels via webhooks.

    Each webhook URL corresponds to one channel.
    Create webhooks at: Server Settings > Integrations > Webhooks
    """

    platform_name = "Discord"
    requires_keys = ["discord_webhook_urls"]  # Comma-separated webhook URLs

    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        urls = credentials.get("discord_webhook_urls", "")
        return bool(urls.strip())

    def _parse_webhook_urls(self, credentials: dict[str, str]) -> list[str]:
        """Parse comma-separated webhook URLs."""
        raw = credentials.get("discord_webhook_urls", "")
        return [url.strip() for url in raw.split(",") if url.strip()]

    def publish(self, title: str, body: str, credentials: dict[str, str], **kwargs) -> PostResult:
        """Post to Discord via webhook(s)."""
        webhook_urls = self._parse_webhook_urls(credentials)

        if not webhook_urls:
            return PostResult(
                platform="Discord",
                success=False,
                error="No Discord webhook URLs configured.",
            )

        results = []
        for i, webhook_url in enumerate(webhook_urls):
            # Discord webhook payload
            # Content limit is 2000 chars
            content = body[:2000] if body else title

            payload = {
                "content": content,
                "username": kwargs.get("username", "StarMaker"),
            }

            try:
                resp = requests.post(
                    webhook_url,
                    json=payload,
                    timeout=10,
                )

                if resp.status_code in (200, 204):
                    results.append(f"Webhook {i + 1}: posted successfully")
                else:
                    results.append(f"Webhook {i + 1}: HTTP {resp.status_code}")
            except requests.RequestException as e:
                results.append(f"Webhook {i + 1}: error - {e}")

        success_count = sum(1 for r in results if "successfully" in r)
        all_success = success_count == len(webhook_urls)

        return PostResult(
            platform="Discord",
            success=all_success,
            message=f"Posted to {success_count}/{len(webhook_urls)} webhook(s). "
                    + "; ".join(results),
            error="" if all_success else "; ".join(r for r in results if "successfully" not in r),
        )
