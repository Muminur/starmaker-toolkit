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
import warnings
from pathlib import Path

import yaml
from dotenv import dotenv_values


CREDENTIALS_DIR = Path.home() / ".starmaker"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.yaml"

# Tracks whether the plaintext-storage warning has already been emitted so it
# fires at most once per process instead of on every load.
_warned_plaintext = False


class PlaintextCredentialsWarning(UserWarning):
    """Warns that credentials.yaml stores secrets unencrypted on disk.

    Subclassed from UserWarning so consumers can filter it precisely via
    ``warnings.filterwarnings("ignore", category=PlaintextCredentialsWarning)``.
    """

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


def _warn_plaintext_once() -> None:
    """Emit a one-time warning that credentials.yaml is stored in plaintext."""
    global _warned_plaintext
    if _warned_plaintext:
        return
    _warned_plaintext = True
    warnings.warn(
        "Credentials are stored unencrypted in credentials.yaml. "
        "Prefer environment variables or a .env file for sensitive values, "
        "and never commit the file to version control.",
        PlaintextCredentialsWarning,
        stacklevel=3,
    )


def _load_yaml_credentials(credentials_dir: Path | None = None) -> dict[str, str]:
    """Load and normalize credentials from credentials.yaml.

    Returns an empty dict when the file is absent. All values are coerced to
    strings (None/empty become ""). Emits a one-time plaintext-storage warning
    only when the file exists and contains data.
    """
    creds_dir = credentials_dir or CREDENTIALS_DIR
    creds_file = creds_dir / "credentials.yaml"
    if not creds_file.exists():
        return {}

    with open(creds_file, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if data:
        _warn_plaintext_once()

    return {k: str(v) if v else "" for k, v in data.items()}


def _load_dotenv_data(dotenv_path: Path | None = None) -> dict[str, str]:
    """Load env-var-style key/value pairs from a .env file.

    When ``dotenv_path`` is None, falls back to ``.env`` in the current working
    directory. Missing files yield an empty dict. Empty/None values are
    filtered out so they never override lower-priority sources.
    """
    if dotenv_path is None:
        dotenv_path = Path.cwd() / ".env"

    if not dotenv_path.exists():
        return {}

    raw: dict[str, str | None] = dotenv_values(dotenv_path)
    return {k: v for k, v in raw.items() if v}


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
    # --- Layer 1: YAML (lowest priority) ---
    result: dict[str, str] = _load_yaml_credentials(credentials_dir)

    # --- Layer 2: .env file (medium priority) ---
    dotenv_data = _load_dotenv_data(dotenv_path)
    known_env_vars = {_yaml_key_to_env_var(k) for k in CREDENTIALS_TEMPLATE}
    for env_key, val in dotenv_data.items():
        if env_key in known_env_vars:  # already filtered to non-empty
            result[_env_var_to_yaml_key(env_key)] = val

    # --- Layer 3: Real environment variables (highest priority) ---
    for yaml_key in CREDENTIALS_TEMPLATE:
        env_val = os.environ.get(_yaml_key_to_env_var(yaml_key), "")
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
    yaml_data = _load_yaml_credentials(credentials_dir)
    dotenv_data = _load_dotenv_data(dotenv_path)

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
