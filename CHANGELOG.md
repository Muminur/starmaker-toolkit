# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `CONTRIBUTING.md`, `DEVELOPMENT.md`, and this `CHANGELOG.md`.
- Continuous integration: GitHub Actions workflow running ruff, pytest (with
  coverage), and mypy across Python 3.9–3.12; pre-commit hooks; `.editorconfig`
  and `.gitattributes`.
- Tooling configuration in `pyproject.toml`: ruff lint rule selection, mypy
  settings, a coverage gate, and conservative dependency upper bounds.
- Optional `seed` argument on the NLP humanizer for deterministic, reproducible
  draft output.
- Config validation: a clear error (not a traceback) on a missing project name
  or malformed repository URL, and a one-time warning that
  `~/.starmaker/credentials.yaml` is stored in plaintext.
- Automatic retry/backoff and rate-limit awareness for GitHub API requests.
- Test coverage for the publishers, platform generators, utils, config, command,
  and CLI modules (suite grew well beyond the original 100 tests).

### Changed
- HTTP `User-Agent` strings are now derived from the package `__version__`
  instead of being hardcoded.
- The interactive menu now dispatches through an explicit command registry
  rather than a fragile `globals()` lookup.
- Awesome-list tag matching is now case-insensitive.
- Draft filenames and platform identifiers are centralized in a single
  constants module within the commands package.

### Fixed
- Narrowed broad `except Exception` handlers across publishers and the setup
  wizard so unexpected errors are no longer silently swallowed.
- `make_table` now validates row width instead of silently dropping data.
- The Rich console UTF-8 wrapper falls back gracefully when stdout has no
  buffer (e.g. under test capture).
- Explicitly passing an unknown `--platform` now fails loudly with the list of
  valid platforms instead of being silently skipped.

## [0.2.0] — Alpha

Initial public alpha release.

### Added

- **CLI** (`starmaker`) built on Click and Rich, with an interactive menu when
  run without a subcommand. Commands:
  - `init` — interactive wizard that generates a `starmaker.yaml` config,
    auto-detecting project details from the local git repo.
  - `draft` — generate platform-specific promotional post drafts (Reddit,
    Hacker News, Dev.to, Twitter/X, Discord).
  - `post` — publish drafts to platforms via their official APIs, with
    `--dry-run` and confirmation prompts.
  - `auto-post` — generate (and optionally publish) posts directly from a
    `README.md` using pure-Python NLP, with `--dry-run` and `--publish`.
  - `audit` — score a repository for star-worthiness and suggest improvements,
    for the local repo or any GitHub URL via `--url`.
  - `awesome` — find matching awesome-lists and generate PR content.
  - `compare` — generate a feature comparison table versus competitors.
  - `readme` — analyze a README and suggest enhancements.
  - `credentials` — show configured API credentials and their source.
  - `setup` — browser-based credential setup wizard.
  - `all` — run audit, draft, awesome, compare, and readme in sequence.
- **NLP post generation** (`starmaker/nlp/`): a README parser that extracts the
  title, tagline, highlights, sections, and inferred technology tags, plus a
  template-based humanizer that produces natural, platform-specific drafts with
  no LLM or external API.
- **Platform generators** (`starmaker/platforms/`): template generators for
  Reddit, Hacker News, Dev.to, Twitter/X, and Discord drafts.
- **Publishers** (`starmaker/publishers/`): publisher classes for Reddit,
  Hacker News, Dev.to, Twitter/X, and Discord that post via official APIs,
  webhooks, or a Camoufox browser flow.
- **Multi-source credential loading** (`starmaker/credentials.py`): credentials
  are resolved with priority environment variables > `.env` file >
  `~/.starmaker/credentials.yaml`, with file-permission hardening on the YAML
  store.
- **Setup wizard** (`starmaker/setup_wizard/`): Camoufox-driven browser flows to
  create platform API apps and extract credentials, plus credential testing.
- **Configuration** (`starmaker/config.py`): `starmaker.yaml` loader with parent
  directory discovery and local git repo detection.
- **One-click installers**: `install.sh` (Linux/macOS) and `install.ps1`
  (Windows).
- **Test suite**: 100 tests covering the README parser, humanizer, credential
  loading, and auto-post flow.

[Unreleased]: https://github.com/Muminur/starmaker-toolkit/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Muminur/starmaker-toolkit/releases/tag/v0.2.0
