"""Base publisher interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PostResult:
    """Result of a publishing attempt."""

    platform: str
    success: bool
    url: str = ""
    message: str = ""
    error: str = ""


class BasePublisher(ABC):
    """Base class for platform publishers.

    Subclasses override ``requires_keys`` with the credential keys they need.
    An immutable tuple is used as the default so subclasses cannot accidentally
    mutate a shared class-level list.
    """

    platform_name: str = ""
    # Immutable default to avoid a shared-mutable-state bug across instances.
    requires_keys: tuple[str, ...] = ()

    @abstractmethod
    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        """Check if required credentials are present and valid.

        Args:
            credentials: Mapping of credential key to value.

        Returns:
            True if the publisher has everything it needs to publish.
        """
        ...

    @abstractmethod
    def publish(self, title: str, body: str, credentials: dict[str, str], **kwargs) -> PostResult:
        """Publish content to the platform.

        Args:
            title: Post title.
            body: Post body/content.
            credentials: Mapping of credential key to value.
            **kwargs: Platform-specific options (e.g. ``subreddit``, ``tags``).

        Returns:
            A :class:`PostResult` describing the outcome.
        """
        ...

    def get_missing_keys(self, credentials: dict[str, str]) -> list[str]:
        """Return the list of required credential keys that are absent or empty.

        Args:
            credentials: Mapping of credential key to value.

        Returns:
            Required keys for which no truthy value was supplied.
        """
        return [k for k in self.requires_keys if not credentials.get(k)]
