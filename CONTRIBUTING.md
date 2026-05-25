# Contributing to StarMaker

Thanks for your interest in improving StarMaker! This guide covers how to set up
a development environment, run the test suite, lint, and submit changes.

StarMaker is an alpha-stage project (`0.2.0`), so APIs and internals may still
shift. Contributions of all sizes are welcome.

## Development Setup

StarMaker requires **Python 3.9+**.

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/Muminur/starmaker-toolkit.git
   cd starmaker-toolkit
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Linux/macOS
   .venv\Scripts\Activate.ps1     # Windows (PowerShell)
   ```

3. Install the package in editable mode with the development extras:
   ```bash
   pip install -e ".[dev]"
   ```

   The `dev` extra installs `pytest`, `pytest-cov`, and `ruff`.

   If you are working on the browser-automation features (the `setup` command
   and the Hacker News / Twitter publishers), also install the `browser` extra:
   ```bash
   pip install -e ".[dev,browser]"
   ```

## Running Tests

The test suite uses `pytest` and lives in `tests/`:

```bash
# Run all tests, quiet output
pytest -q

# Run with coverage for the starmaker package
pytest --cov=starmaker

# Run a single test file
pytest tests/test_readme_parser.py
```

All tests should pass before you open a pull request. Add tests for any new
behavior or bug fix.

## Linting

StarMaker uses [Ruff](https://docs.astral.sh/ruff/) for linting. Configuration
lives in `pyproject.toml` (`line-length = 100`, `target-version = "py39"`).

```bash
# Check the whole project
ruff check .

# Auto-fix what can be fixed
ruff check . --fix
```

Run `ruff check .` and make sure it is clean before committing.

## Code Style

- **Type hints:** All new functions and methods should be fully type-hinted.
  The codebase uses `from __future__ import annotations` so modern syntax
  (e.g. `str | None`) is fine on Python 3.9.
- **Docstrings:** Every module, public function, and class should have a short
  docstring describing its purpose.
- **No bare excepts:** Always catch specific exceptions
  (e.g. `except (OSError, ValueError):`). Never write a bare `except:`.
- **Line length:** Keep lines within 100 characters.
- **Imports:** Prefer importing heavy or optional dependencies lazily inside the
  command functions that need them (this is how `cli.py` keeps startup fast and
  avoids hard-failing when an optional extra is missing).
- **Console output:** Use the shared Rich console from
  `starmaker.utils.console` rather than bare `print()`.
- **Secrets:** Never hardcode API keys, tokens, or passwords. Credentials are
  loaded at runtime from environment variables, a `.env` file, or
  `~/.starmaker/credentials.yaml` (see `starmaker/credentials.py`). Never commit
  a `.env` file or `credentials.yaml`.

For an overview of how the codebase is organized, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Branch & Commit Conventions

- Create a feature branch off `main`; do not commit directly to `main`.
- Use [Conventional Commits](https://www.conventionalcommits.org/) for commit
  messages and PR titles. Common prefixes:
  - `feat:` — a new feature
  - `fix:` — a bug fix
  - `docs:` — documentation only
  - `refactor:` — code change that neither fixes a bug nor adds a feature
  - `test:` — adding or fixing tests
  - `chore:` — tooling, build, or housekeeping

  Example: `feat(publishers): add Mastodon publisher`

## Pull Requests

1. Make sure `pytest -q` passes and `ruff check .` is clean.
2. Update the `[Unreleased]` section of [CHANGELOG.md](CHANGELOG.md) describing
   your change.
3. Update relevant documentation (README, DEVELOPMENT, docstrings) if behavior
   changes.
4. Open a PR against `main` with a descriptive Conventional-Commits title and a
   summary of what changed and why.

## Reporting Issues

When filing a bug report, please include your OS, Python version, the command
you ran, and the full error output. For feature requests, describe the use case
you are trying to support.
