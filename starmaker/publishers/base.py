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
    """Base class for platform publishers."""

    platform_name: str = ""
    requires_keys: list[str] = []

    @abstractmethod
    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        """Check if required credentials are present and valid."""
        ...

    @abstractmethod
    def publish(self, title: str, body: str, credentials: dict[str, str], **kwargs) -> PostResult:
        """Publish content to the platform."""
        ...

    def get_missing_keys(self, credentials: dict[str, str]) -> list[str]:
        """Return list of missing credential keys."""
        return [k for k in self.requires_keys if not credentials.get(k)]
