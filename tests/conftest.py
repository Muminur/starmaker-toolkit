"""Shared pytest fixtures for starmaker-toolkit tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all platform-related env vars to ensure a clean slate."""
    for key in list(os.environ.keys()):
        if key.startswith(("REDDIT_", "DEVTO_", "TWITTER_", "DISCORD_")):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def tmp_credentials_dir(tmp_path):
    """Create a temporary .starmaker credentials directory."""
    creds_dir = tmp_path / ".starmaker"
    creds_dir.mkdir()
    return creds_dir
