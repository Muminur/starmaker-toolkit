"""Credentials manager for platform API keys.

Stores credentials in ~/.starmaker/credentials.yaml (user's home directory).
This file should NEVER be committed to git.
"""

from __future__ import annotations

from pathlib import Path

import yaml


CREDENTIALS_DIR = Path.home() / ".starmaker"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.yaml"

# Template with all supported credential fields
CREDENTIALS_TEMPLATE = {
    # Reddit — Create app at https://www.reddit.com/prefs/apps/ (script type)
    "reddit_client_id": "",
    "reddit_client_secret": "",
    "reddit_username": "",
    "reddit_password": "",

    # Dev.to — Get API key at https://dev.to/settings/extensions
    "devto_api_key": "",

    # Twitter/X — Get keys at https://developer.twitter.com/en/portal/dashboard
    # Note: Twitter API v2 requires a paid Basic plan ($100/mo)
    # Leave blank to use free browser intent instead
    "twitter_api_key": "",
    "twitter_api_secret": "",
    "twitter_access_token": "",
    "twitter_access_secret": "",
    "twitter_bearer_token": "",
    "twitter_username": "",

    # Discord — Create webhooks at Server Settings > Integrations > Webhooks
    # Comma-separated URLs for multiple channels/servers
    "discord_webhook_urls": "",
}


def ensure_credentials_dir() -> None:
    """Create credentials directory if it doesn't exist."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

    # Create .gitignore in credentials dir
    gitignore = CREDENTIALS_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n", encoding="utf-8")


def load_credentials() -> dict[str, str]:
    """Load credentials from file."""
    if not CREDENTIALS_FILE.exists():
        return {}

    with open(CREDENTIALS_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return {k: str(v) if v else "" for k, v in data.items()}


def save_credentials(credentials: dict[str, str]) -> None:
    """Save credentials to file."""
    ensure_credentials_dir()

    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(credentials, f, default_flow_style=False, sort_keys=False)


def init_credentials() -> Path:
    """Create credentials file with template if it doesn't exist."""
    ensure_credentials_dir()

    if not CREDENTIALS_FILE.exists():
        save_credentials(CREDENTIALS_TEMPLATE)

    return CREDENTIALS_FILE


def get_credential(key: str) -> str:
    """Get a single credential value."""
    creds = load_credentials()
    return creds.get(key, "")


def set_credential(key: str, value: str) -> None:
    """Set a single credential value."""
    creds = load_credentials()
    creds[key] = value
    save_credentials(creds)
