"""Dev.to publisher using official API.

API docs: https://developers.forem.com/api/v1
"""

from __future__ import annotations

import requests

from starmaker.publishers.base import BasePublisher, PostResult


class DevtoPublisher(BasePublisher):
    """Publish articles to Dev.to via official API.

    Get your API key at: https://dev.to/settings/extensions
    """

    platform_name = "Dev.to"
    requires_keys = ["devto_api_key"]

    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        missing = self.get_missing_keys(credentials)
        return len(missing) == 0

    def publish(self, title: str, body: str, credentials: dict[str, str], **kwargs) -> PostResult:
        """Create a draft article on Dev.to."""
        api_key = credentials["devto_api_key"]
        tags = kwargs.get("tags", [])
        published = kwargs.get("published", False)

        headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
        }

        article_data = {
            "article": {
                "title": title,
                "body_markdown": body,
                "published": published,
                "tags": tags[:4],  # Dev.to max 4 tags
            }
        }

        resp = requests.post(
            "https://dev.to/api/articles",
            headers=headers,
            json=article_data,
            timeout=15,
        )

        if resp.status_code in (200, 201):
            data = resp.json()
            post_url = data.get("url", "")
            status = "published" if published else "saved as draft"
            return PostResult(
                platform="Dev.to",
                success=True,
                url=post_url,
                message=f"Article {status} on Dev.to",
            )

        return PostResult(
            platform="Dev.to",
            success=False,
            error=f"HTTP {resp.status_code}: {resp.text[:200]}",
        )
