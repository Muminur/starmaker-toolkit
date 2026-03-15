"""TDD tests for the credential loading system.

Tests the multi-source credential loading interface:
  1. Environment variables (highest priority)
  2. .env file via python-dotenv (medium priority)
  3. ~/.starmaker/credentials.yaml (lowest priority, backward compat)

These tests are written BEFORE the implementation. They will fail until
load_credentials(), _yaml_key_to_env_var(), _env_var_to_yaml_key(), and
get_credential_sources() are added/updated in starmaker/credentials.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helper: import new functions with a clear skip message if not yet implemented
# ---------------------------------------------------------------------------

def _import_yaml_key_to_env_var():
    from starmaker.credentials import _yaml_key_to_env_var  # noqa: PLC0415
    return _yaml_key_to_env_var


def _import_env_var_to_yaml_key():
    from starmaker.credentials import _env_var_to_yaml_key  # noqa: PLC0415
    return _env_var_to_yaml_key


def _import_load_credentials():
    from starmaker.credentials import load_credentials  # noqa: PLC0415
    return load_credentials


def _import_get_credential_sources():
    from starmaker.credentials import get_credential_sources  # noqa: PLC0415
    return get_credential_sources


def _import_save_credentials():
    from starmaker.credentials import save_credentials  # noqa: PLC0415
    return save_credentials


def _import_init_credentials():
    from starmaker.credentials import init_credentials  # noqa: PLC0415
    return init_credentials


# ---------------------------------------------------------------------------
# TestCredentialKeyMapping
# ---------------------------------------------------------------------------

class TestCredentialKeyMapping:
    """Test bidirectional mapping between YAML keys and env var names."""

    def test_yaml_key_to_env_var_name(self):
        """reddit_client_id -> REDDIT_CLIENT_ID"""
        _yaml_key_to_env_var = pytest.importorskip(
            "starmaker.credentials", reason="module not available"
        )
        fn = _import_yaml_key_to_env_var()
        assert fn("reddit_client_id") == "REDDIT_CLIENT_ID"

    def test_yaml_key_to_env_var_devto(self):
        """devto_api_key -> DEVTO_API_KEY"""
        fn = _import_yaml_key_to_env_var()
        assert fn("devto_api_key") == "DEVTO_API_KEY"

    def test_yaml_key_to_env_var_discord(self):
        """discord_webhook_urls -> DISCORD_WEBHOOK_URLS"""
        fn = _import_yaml_key_to_env_var()
        assert fn("discord_webhook_urls") == "DISCORD_WEBHOOK_URLS"

    def test_env_var_to_yaml_key(self):
        """REDDIT_CLIENT_ID -> reddit_client_id"""
        fn = _import_env_var_to_yaml_key()
        assert fn("REDDIT_CLIENT_ID") == "reddit_client_id"

    def test_env_var_to_yaml_key_devto(self):
        """DEVTO_API_KEY -> devto_api_key"""
        fn = _import_env_var_to_yaml_key()
        assert fn("DEVTO_API_KEY") == "devto_api_key"

    def test_roundtrip_yaml_to_env_and_back(self):
        """yaml_key -> env_var -> yaml_key produces original key."""
        to_env = _import_yaml_key_to_env_var()
        to_yaml = _import_env_var_to_yaml_key()
        original = "twitter_access_token"
        assert to_yaml(to_env(original)) == original

    def test_roundtrip_env_to_yaml_and_back(self):
        """env_var -> yaml_key -> env_var produces original name."""
        to_env = _import_yaml_key_to_env_var()
        to_yaml = _import_env_var_to_yaml_key()
        original = "TWITTER_API_KEY"
        assert to_env(to_yaml(original)) == original


# ---------------------------------------------------------------------------
# TestLoadingPriority
# ---------------------------------------------------------------------------

class TestLoadingPriority:
    """Test the three-tier priority: env > dotenv > yaml."""

    def test_env_var_overrides_dotenv(self, monkeypatch, tmp_path, clean_env):
        """Real env vars take precedence over .env file values."""
        env_file = tmp_path / ".env"
        env_file.write_text("REDDIT_CLIENT_ID=from_dotenv\n")
        monkeypatch.setenv("REDDIT_CLIENT_ID", "from_env")

        load_credentials = _import_load_credentials()
        creds = load_credentials(dotenv_path=env_file)
        assert creds["reddit_client_id"] == "from_env"

    def test_dotenv_overrides_yaml(self, tmp_path, clean_env):
        """Dotenv values take precedence over YAML file values."""
        # Write YAML credentials
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()
        (creds_dir / "credentials.yaml").write_text(
            yaml.dump({"reddit_client_id": "from_yaml"})
        )
        # Write .env with a different value
        env_file = tmp_path / ".env"
        env_file.write_text("REDDIT_CLIENT_ID=from_dotenv\n")

        load_credentials = _import_load_credentials()
        creds = load_credentials(credentials_dir=creds_dir, dotenv_path=env_file)
        assert creds["reddit_client_id"] == "from_dotenv"

    def test_yaml_used_as_fallback(self, tmp_path, clean_env):
        """YAML values are used when no env var or dotenv value exists."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()
        (creds_dir / "credentials.yaml").write_text(
            yaml.dump({"reddit_client_secret": "yaml_secret"})
        )

        load_credentials = _import_load_credentials()
        creds = load_credentials(credentials_dir=creds_dir)
        assert creds["reddit_client_secret"] == "yaml_secret"

    def test_env_var_overrides_yaml(self, monkeypatch, tmp_path, clean_env):
        """Real env vars take precedence over YAML file values."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()
        (creds_dir / "credentials.yaml").write_text(
            yaml.dump({"reddit_client_id": "from_yaml"})
        )
        monkeypatch.setenv("REDDIT_CLIENT_ID", "from_env")

        load_credentials = _import_load_credentials()
        creds = load_credentials(credentials_dir=creds_dir)
        assert creds["reddit_client_id"] == "from_env"

    def test_empty_env_var_not_treated_as_set(self, monkeypatch, tmp_path, clean_env):
        """An empty string env var must not override a YAML value."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()
        (creds_dir / "credentials.yaml").write_text(
            yaml.dump({"reddit_client_id": "from_yaml"})
        )
        monkeypatch.setenv("REDDIT_CLIENT_ID", "")

        load_credentials = _import_load_credentials()
        creds = load_credentials(credentials_dir=creds_dir)
        assert creds["reddit_client_id"] == "from_yaml"

    def test_all_three_sources_merged(self, monkeypatch, tmp_path, clean_env):
        """Keys from all three sources appear in the result (lower-priority
        keys not present in higher-priority sources are still included)."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()
        (creds_dir / "credentials.yaml").write_text(
            yaml.dump({
                "reddit_client_id": "yaml_id",
                "reddit_client_secret": "yaml_secret",
            })
        )
        env_file = tmp_path / ".env"
        env_file.write_text("DEVTO_API_KEY=dotenv_devto\n")
        monkeypatch.setenv("REDDIT_CLIENT_ID", "env_id")

        load_credentials = _import_load_credentials()
        creds = load_credentials(credentials_dir=creds_dir, dotenv_path=env_file)

        assert creds["reddit_client_id"] == "env_id"        # env wins
        assert creds["reddit_client_secret"] == "yaml_secret"  # yaml fallback
        assert creds["devto_api_key"] == "dotenv_devto"         # dotenv only


# ---------------------------------------------------------------------------
# TestBackwardCompatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    """Existing credentials.yaml files must continue to work unchanged."""

    def test_existing_yaml_still_works(self, tmp_path, clean_env):
        """Existing credentials.yaml files continue to work."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()
        (creds_dir / "credentials.yaml").write_text(
            yaml.dump({
                "reddit_client_id": "test_id",
                "reddit_client_secret": "test_secret",
            })
        )

        load_credentials = _import_load_credentials()
        creds = load_credentials(credentials_dir=creds_dir)
        assert creds["reddit_client_id"] == "test_id"
        assert creds["reddit_client_secret"] == "test_secret"

    def test_load_returns_dict_with_string_values(self, tmp_path, clean_env):
        """All returned values are strings, never None."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()
        # Write YAML with a null/None value
        (creds_dir / "credentials.yaml").write_text(
            "reddit_client_id: test\nreddit_client_secret:\n"
        )

        load_credentials = _import_load_credentials()
        creds = load_credentials(credentials_dir=creds_dir)
        for val in creds.values():
            assert isinstance(val, str), f"Expected str, got {type(val)}: {val!r}"

    def test_missing_yaml_returns_empty_dict(self, tmp_path, clean_env):
        """No YAML file is not an error; returns empty dict."""
        empty_dir = tmp_path / ".starmaker"
        empty_dir.mkdir()

        load_credentials = _import_load_credentials()
        creds = load_credentials(credentials_dir=empty_dir)
        assert isinstance(creds, dict)

    def test_load_without_args_does_not_raise(self, clean_env):
        """Calling load_credentials() with no args should not raise."""
        load_credentials = _import_load_credentials()
        # May return empty dict if no file exists; should not raise
        result = load_credentials()
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# TestDotenvLoading
# ---------------------------------------------------------------------------

class TestDotenvLoading:
    """Test .env file loading behaviour."""

    def test_loads_from_dotenv_file(self, tmp_path, clean_env):
        """Values from .env file are loaded correctly."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "REDDIT_CLIENT_ID=my_client_id\n"
            "REDDIT_CLIENT_SECRET=my_secret\n"
        )

        load_credentials = _import_load_credentials()
        creds = load_credentials(dotenv_path=env_file)
        assert creds["reddit_client_id"] == "my_client_id"
        assert creds["reddit_client_secret"] == "my_secret"

    def test_missing_dotenv_file_is_ok(self, clean_env):
        """No error when .env file doesn't exist."""
        load_credentials = _import_load_credentials()
        # Should not raise
        creds = load_credentials(dotenv_path=Path("/nonexistent/.env"))
        assert isinstance(creds, dict)

    def test_dotenv_with_double_quotes(self, tmp_path, clean_env):
        """Double-quoted values in .env are handled correctly."""
        env_file = tmp_path / ".env"
        env_file.write_text('REDDIT_CLIENT_SECRET="my secret with spaces"\n')

        load_credentials = _import_load_credentials()
        creds = load_credentials(dotenv_path=env_file)
        assert creds["reddit_client_secret"] == "my secret with spaces"

    def test_dotenv_with_single_quotes(self, tmp_path, clean_env):
        """Single-quoted values in .env are handled correctly."""
        env_file = tmp_path / ".env"
        env_file.write_text("REDDIT_CLIENT_SECRET='my secret'\n")

        load_credentials = _import_load_credentials()
        creds = load_credentials(dotenv_path=env_file)
        assert creds["reddit_client_secret"] == "my secret"

    def test_dotenv_with_hash_in_value(self, tmp_path, clean_env):
        """Values with # character are handled (common in passwords)."""
        env_file = tmp_path / ".env"
        env_file.write_text("REDDIT_PASSWORD='pass#word123'\n")

        load_credentials = _import_load_credentials()
        creds = load_credentials(dotenv_path=env_file)
        assert creds["reddit_password"] == "pass#word123"

    def test_dotenv_keys_converted_to_yaml_keys(self, tmp_path, clean_env):
        """Env-var-style keys from .env are returned as lowercase yaml keys."""
        env_file = tmp_path / ".env"
        env_file.write_text("TWITTER_BEARER_TOKEN=tok123\n")

        load_credentials = _import_load_credentials()
        creds = load_credentials(dotenv_path=env_file)
        assert "twitter_bearer_token" in creds
        assert creds["twitter_bearer_token"] == "tok123"

    def test_dotenv_empty_value_not_included(self, tmp_path, clean_env):
        """Empty values in .env file do not override lower-priority sources."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()
        (creds_dir / "credentials.yaml").write_text(
            yaml.dump({"reddit_client_id": "from_yaml"})
        )
        env_file = tmp_path / ".env"
        env_file.write_text("REDDIT_CLIENT_ID=\n")

        load_credentials = _import_load_credentials()
        creds = load_credentials(credentials_dir=creds_dir, dotenv_path=env_file)
        # Empty dotenv value should not override YAML
        assert creds["reddit_client_id"] == "from_yaml"


# ---------------------------------------------------------------------------
# TestCredentialSource
# ---------------------------------------------------------------------------

class TestCredentialSource:
    """Test that get_credential_sources() identifies where each key came from."""

    def test_get_credential_sources_identifies_env(self, monkeypatch, clean_env):
        """get_credential_sources correctly identifies env var source."""
        monkeypatch.setenv("REDDIT_CLIENT_ID", "from_env")

        get_credential_sources = _import_get_credential_sources()
        sources = get_credential_sources()
        assert sources.get("reddit_client_id") == "env"

    def test_get_credential_sources_identifies_dotenv(self, tmp_path, clean_env):
        """get_credential_sources correctly identifies .env source."""
        env_file = tmp_path / ".env"
        env_file.write_text("DEVTO_API_KEY=from_dotenv\n")

        get_credential_sources = _import_get_credential_sources()
        sources = get_credential_sources(dotenv_path=env_file)
        assert sources.get("devto_api_key") == "dotenv"

    def test_get_credential_sources_identifies_yaml(self, tmp_path, clean_env):
        """get_credential_sources correctly identifies yaml source."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()
        (creds_dir / "credentials.yaml").write_text(
            yaml.dump({"reddit_client_secret": "secret"})
        )

        get_credential_sources = _import_get_credential_sources()
        sources = get_credential_sources(credentials_dir=creds_dir)
        assert sources.get("reddit_client_secret") == "yaml"

    def test_get_credential_sources_identifies_unset(self, tmp_path, clean_env):
        """get_credential_sources correctly identifies unset credentials."""
        empty_dir = tmp_path / ".starmaker"
        empty_dir.mkdir()

        get_credential_sources = _import_get_credential_sources()
        sources = get_credential_sources(credentials_dir=empty_dir)
        # All known template keys not found anywhere should be "unset"
        assert sources.get("reddit_client_id") in ("unset", None)

    def test_get_credential_sources_env_beats_dotenv_source(
        self, monkeypatch, tmp_path, clean_env
    ):
        """When env var exists, source is 'env' even if also in .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("REDDIT_CLIENT_ID=dotenv_val\n")
        monkeypatch.setenv("REDDIT_CLIENT_ID", "env_val")

        get_credential_sources = _import_get_credential_sources()
        sources = get_credential_sources(dotenv_path=env_file)
        assert sources.get("reddit_client_id") == "env"

    def test_get_credential_sources_returns_dict(self, clean_env):
        """get_credential_sources always returns a dict."""
        get_credential_sources = _import_get_credential_sources()
        result = get_credential_sources()
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# TestSaveCredentials
# ---------------------------------------------------------------------------

class TestSaveCredentials:
    """Test save_credentials() behaviour."""

    def test_save_creates_directory(self, tmp_path):
        """save_credentials creates the credentials directory if needed."""
        creds_dir = tmp_path / ".starmaker"
        # Deliberately do NOT pre-create creds_dir

        save_credentials = _import_save_credentials()
        save_credentials(
            {"reddit_client_id": "test"},
            credentials_dir=creds_dir,
        )
        assert creds_dir.exists()

    def test_save_writes_yaml(self, tmp_path):
        """save_credentials writes valid YAML that can be read back."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()

        save_credentials = _import_save_credentials()
        data = {"reddit_client_id": "abc", "devto_api_key": "xyz"}
        save_credentials(data, credentials_dir=creds_dir)

        written = yaml.safe_load((creds_dir / "credentials.yaml").read_text())
        assert written["reddit_client_id"] == "abc"
        assert written["devto_api_key"] == "xyz"

    def test_save_overwrites_existing_file(self, tmp_path):
        """save_credentials replaces the existing file completely."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()
        (creds_dir / "credentials.yaml").write_text(
            yaml.dump({"reddit_client_id": "old"})
        )

        save_credentials = _import_save_credentials()
        save_credentials({"reddit_client_id": "new"}, credentials_dir=creds_dir)

        written = yaml.safe_load((creds_dir / "credentials.yaml").read_text())
        assert written["reddit_client_id"] == "new"

    def test_save_creates_gitignore(self, tmp_path):
        """save_credentials creates a .gitignore in the credentials dir."""
        creds_dir = tmp_path / ".starmaker"

        save_credentials = _import_save_credentials()
        save_credentials({"reddit_client_id": "test"}, credentials_dir=creds_dir)

        gitignore = creds_dir / ".gitignore"
        assert gitignore.exists()


# ---------------------------------------------------------------------------
# TestInitCredentials
# ---------------------------------------------------------------------------

class TestInitCredentials:
    """Test init_credentials() template creation behaviour."""

    def test_creates_template_if_missing(self, tmp_path):
        """init_credentials creates a template file when none exists."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()

        init_credentials = _import_init_credentials()
        result_path = init_credentials(credentials_dir=creds_dir)

        assert result_path.exists()
        data = yaml.safe_load(result_path.read_text())
        # Template must contain at least the reddit keys
        assert "reddit_client_id" in data

    def test_preserves_existing_file(self, tmp_path):
        """init_credentials does not overwrite an existing credentials file."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()
        creds_file = creds_dir / "credentials.yaml"
        creds_file.write_text(yaml.dump({"reddit_client_id": "preserved"}))

        init_credentials = _import_init_credentials()
        init_credentials(credentials_dir=creds_dir)

        data = yaml.safe_load(creds_file.read_text())
        assert data["reddit_client_id"] == "preserved"

    def test_returns_path_to_credentials_file(self, tmp_path):
        """init_credentials returns the Path to the credentials file."""
        creds_dir = tmp_path / ".starmaker"
        creds_dir.mkdir()

        init_credentials = _import_init_credentials()
        result = init_credentials(credentials_dir=creds_dir)

        assert isinstance(result, Path)
        assert result.name == "credentials.yaml"
