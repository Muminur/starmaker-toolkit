"""Credentials manager for platform API keys.

Supports multi-source credential loading with priority:
  1. Environment variables (highest)
  2. .env file via python-dotenv (medium)
  3. ~/.starmaker/credentials.yaml (lowest, backward compat)

The YAML file should NEVER be committed to git.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import yaml
from dotenv import dotenv_values


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


def _yaml_key_to_env_var(key: str) -> str:
    """Convert 'reddit_client_id' to 'REDDIT_CLIENT_ID'."""
    return key.upper()


def _env_var_to_yaml_key(env_var: str) -> str:
    """Convert 'REDDIT_CLIENT_ID' to 'reddit_client_id'."""
    return env_var.lower()


def ensure_credentials_dir(credentials_dir: Path | None = None) -> Path:
    """Create credentials directory if it doesn't exist. Returns the dir path."""
    creds_dir = credentials_dir or CREDENTIALS_DIR
    creds_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitignore in credentials dir
    gitignore = creds_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n", encoding="utf-8")

    return creds_dir


def load_credentials(
    *,
    credentials_dir: Path | None = None,
    dotenv_path: Path | None = None,
) -> dict[str, str]:
    """Load credentials from multiple sources with priority: env > dotenv > yaml.

    Args:
        credentials_dir: Directory containing credentials.yaml.
                         Defaults to ~/.starmaker/.
        dotenv_path: Path to .env file. Defaults to None (searches CWD).

    Returns:
        Dict mapping lowercase yaml keys to string values.
    """
    result: dict[str, str] = {}

    # --- Layer 1: YAML (lowest priority) ---
    creds_dir = credentials_dir or CREDENTIALS_DIR
    creds_file = creds_dir / "credentials.yaml"
    if creds_file.exists():
        with open(creds_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for k, v in data.items():
            result[k] = str(v) if v else ""

    # --- Layer 2: .env file (medium priority) ---
    dotenv_data: dict[str, str | None] = {}
    if dotenv_path is not None:
        if dotenv_path.exists():
            dotenv_data = dotenv_values(dotenv_path)
    else:
        # Default: look for .env in CWD
        cwd_env = Path.cwd() / ".env"
        if cwd_env.exists():
            dotenv_data = dotenv_values(cwd_env)

    # Known env var names from template
    known_env_vars = {_yaml_key_to_env_var(k) for k in CREDENTIALS_TEMPLATE}

    for env_key, val in dotenv_data.items():
        if env_key in known_env_vars and val:  # non-empty only
            yaml_key = _env_var_to_yaml_key(env_key)
            result[yaml_key] = val

    # --- Layer 3: Real environment variables (highest priority) ---
    for yaml_key in CREDENTIALS_TEMPLATE:
        env_key = _yaml_key_to_env_var(yaml_key)
        env_val = os.environ.get(env_key, "")
        if env_val:  # non-empty only
            result[yaml_key] = env_val

    return result


def get_credential_sources(
    *,
    credentials_dir: Path | None = None,
    dotenv_path: Path | None = None,
) -> dict[str, str]:
    """Return a dict mapping each credential key to its source.

    Sources: 'env', 'dotenv', 'yaml', or 'unset'.
    """
    # Load YAML
    creds_dir = credentials_dir or CREDENTIALS_DIR
    creds_file = creds_dir / "credentials.yaml"
    yaml_data: dict[str, str] = {}
    if creds_file.exists():
        with open(creds_file, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        yaml_data = {k: str(v) if v else "" for k, v in raw.items()}

    # Load dotenv
    dotenv_data: dict[str, str | None] = {}
    if dotenv_path is not None:
        if dotenv_path.exists():
            dotenv_data = dotenv_values(dotenv_path)
    else:
        cwd_env = Path.cwd() / ".env"
        if cwd_env.exists():
            dotenv_data = dotenv_values(cwd_env)

    sources: dict[str, str] = {}
    for yaml_key in CREDENTIALS_TEMPLATE:
        env_key = _yaml_key_to_env_var(yaml_key)

        # Check real env (highest priority)
        env_val = os.environ.get(env_key, "")
        if env_val:
            sources[yaml_key] = "env"
            continue

        # Check dotenv
        dotenv_val = dotenv_data.get(env_key)
        if dotenv_val:
            sources[yaml_key] = "dotenv"
            continue

        # Check yaml
        yaml_val = yaml_data.get(yaml_key, "")
        if yaml_val:
            sources[yaml_key] = "yaml"
            continue

        sources[yaml_key] = "unset"

    return sources


def save_credentials(
    credentials: dict[str, str],
    *,
    credentials_dir: Path | None = None,
) -> None:
    """Save credentials to YAML file."""
    creds_dir = ensure_credentials_dir(credentials_dir)
    creds_file = creds_dir / "credentials.yaml"

    with open(creds_file, "w", encoding="utf-8") as f:
        yaml.dump(credentials, f, default_flow_style=False, sort_keys=False)

    # Set restrictive file permissions
    try:
        creds_file.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    except OSError:
        pass  # Windows may not support this


def init_credentials(
    *,
    credentials_dir: Path | None = None,
) -> Path:
    """Create credentials file with template if it doesn't exist.

    Returns path to the credentials file.
    """
    creds_dir = ensure_credentials_dir(credentials_dir)
    creds_file = creds_dir / "credentials.yaml"

    if not creds_file.exists():
        save_credentials(CREDENTIALS_TEMPLATE, credentials_dir=creds_dir)

    return creds_file


def get_credential(key: str) -> str:
    """Get a single credential value."""
    creds = load_credentials()
    return creds.get(key, "")


def set_credential(key: str, value: str) -> None:
    """Set a single credential value."""
    creds = load_credentials()
    creds[key] = value
    save_credentials(creds)
