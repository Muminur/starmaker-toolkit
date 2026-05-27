# Development & Architecture

This document describes how StarMaker is organized internally. It is meant for
contributors; for usage see [README.md](README.md) and for setup/workflow see
[CONTRIBUTING.md](CONTRIBUTING.md).

## High-Level Flow

StarMaker is a Click + Rich command-line application. The entry point is the
`starmaker` console script, which maps to `starmaker.cli:main`.

```
starmaker (CLI)                      starmaker/cli.py
  └─ command dispatch ────────────►  starmaker/commands/*.py
        ├─ draft  ──────────────────► platforms/  (template generators)
        ├─ post / auto-post ────────► publishers/ (official-API posting)
        ├─ auto-post ───────────────► nlp/        (README → drafts)
        ├─ audit ───────────────────► utils/github_api.py
        ├─ awesome / compare / readme
        ├─ credentials ─────────────► credentials.py
        └─ setup ───────────────────► setup_wizard/

        all commands load config ───► config.py
        and resolve secrets via ────► credentials.py
        and print through ──────────► utils/console.py
```

## Module Layout

### `starmaker/cli.py` — command line interface

Defines the Click command group `cli`. Running `starmaker` with no subcommand
calls `_interactive_menu()`, which prints a banner and a numbered menu and then
invokes the chosen command. Each subcommand (`init`, `draft`, `post`,
`auto-post`, `audit`, `awesome`, `compare`, `readme`, `credentials`, `setup`,
`all`) is a thin wrapper: it parses options, loads config where needed, and
delegates to a `run(...)` function in `starmaker/commands/`.

Heavy or optional imports (commands, publishers, the setup wizard) are imported
*lazily inside* each command body so the CLI starts quickly and does not fail
when an optional extra (e.g. `browser`) is not installed.

The version is defined once in `starmaker/__init__.py` as
`__version__` and surfaced via `--version`.

### `starmaker/commands/` — command implementations

One module per user-facing command, each exposing a `run(...)` function:

- `audit.py` — fetches repository data and scores it for star-worthiness.
- `draft_posts.py` — iterates the configured platforms and writes draft files
  using the `PLATFORMS` generators.
- `post.py` — parses draft files and publishes them through `PUBLISHERS`,
  supporting dry-run and confirmation.
- `auto_post.py` — runs the NLP pipeline on a README and optionally publishes.
- `awesome.py` — finds awesome-lists and generates PR content.
- `compare.py` — builds a feature comparison table.
- `readme.py` — analyzes a README and suggests enhancements.

### `starmaker/platforms/` — draft template generators

Pure template/formatting code (no network). `platforms/__init__.py` exposes a
`PLATFORMS` dict mapping a platform name to a `generate(...)` function for
Reddit, Hacker News, Dev.to, Twitter/X, and Discord. These produce the draft
text that `draft` writes to disk; they do **not** post anything.

### `starmaker/publishers/` — official-API publishing

`publishers/__init__.py` exposes a `PUBLISHERS` dict mapping a platform name to
a publisher class. Each publisher subclasses `BasePublisher`
(`publishers/base.py`), declares `platform_name` and `requires_keys`, and
returns a `PostResult` dataclass (`platform`, `success`, `url`, `message`,
`error`). Publishers exist for Reddit, Hacker News, Dev.to, Twitter/X, and
Discord. Browser-based flows (e.g. Hacker News) use the Camoufox helper in
`publishers/_camoufox_open.py` and require the `browser` extra.

### `starmaker/nlp/` — README summarization (no LLM)

Pure-Python text processing, no AI/LLM or external NLP libraries:

- `readme_parser.py` — parses a README into a `ReadmeContent` dataclass
  (title, tagline, description, sections, highlights, repo URL), infers
  technology tags, and can build a `StarMakerConfig` from a README via
  `build_config_from_readme()`.
- `humanizer.py` — turns `ReadmeContent` into natural, platform-specific drafts
  using randomized template pools (`generate_all_drafts`). Its output formats
  match exactly what the `post` command's draft parsers expect.

### `starmaker/config.py` — configuration

Dataclasses `ProjectConfig`, `AuthorConfig`, `PromotionConfig`, and the root
`StarMakerConfig`. `find_config()` walks the current directory and its parents
looking for `starmaker.yaml`; `load_config()` parses it (returning defaults if
absent); `detect_local_repo()` shells out to `git remote get-url origin` to
auto-detect the repo URL, owner, and name.

### `starmaker/credentials.py` — secrets management

Resolves credentials from three sources, highest priority first:

1. Environment variables (e.g. `REDDIT_CLIENT_ID`)
2. A `.env` file in the current directory (via `python-dotenv`)
3. `~/.starmaker/credentials.yaml` (legacy, backward compatible)

Only non-empty values from a higher-priority source override lower ones.
`CREDENTIALS_TEMPLATE` is the canonical list of supported keys (mapped to
uppercase env-var names). `get_credential_sources()` reports where each value
came from (`env` / `dotenv` / `yaml` / `unset`), which powers the `credentials`
command's status table. `save_credentials()` writes the YAML store with
`0o600` permissions where the OS supports it.

### `starmaker/setup_wizard/` — browser credential wizard

Drives the `setup` command. `wizard.py` orchestrates per-platform setup flows
(`reddit_setup.py`, `devto_setup.py`, `discord_setup.py`) using a Camoufox
browser (`browser.py`) to help create API apps and extract credentials, then
tests them (`test_all_credentials`). Requires the `browser` extra.

### `starmaker/utils/` — shared helpers

- `console.py` — the shared Rich `console` used for all output.
- `github_api.py` — GitHub REST and local git analysis, aggregated into a
  `RepoInfo` dataclass (used by `audit`).
- `markdown.py` — small markdown builders (`make_table`, `make_badge`, etc.).

## Tests

Tests live in `tests/` and run with `pytest`. They cover the README parser,
the humanizer, credential loading/source resolution, and the auto-post flow.
See [CONTRIBUTING.md](CONTRIBUTING.md) for how to run them.

## Adding a New Platform

A new platform typically touches three places:

1. `platforms/<name>.py` — a `generate(...)` function, registered in
   `platforms/__init__.py`'s `PLATFORMS` dict (for `draft`).
2. `publishers/<name>_publisher.py` — a `BasePublisher` subclass returning a
   `PostResult`, registered in `publishers/__init__.py`'s `PUBLISHERS` dict
   (for `post`).
3. `credentials.py` — add any new keys to `CREDENTIALS_TEMPLATE`, and update the
   `credentials` command's platform map in `cli.py` if it needs API keys.
