# StarMaker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Universal OSS promotion toolkit. Generate promotional post drafts, auto-post from your README using pure Python NLP, audit your repo for star-worthiness, find awesome-lists, create comparison tables, and enhance your README — all without any AI or LLM.

## One-Click Install

```bash
# Linux/macOS
curl -sSL https://raw.githubusercontent.com/Muminur/starmaker-toolkit/main/install.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/Muminur/starmaker-toolkit/main/install.ps1 | iex

# Or install manually
pip install -e ".[browser]"
```

## Quick Start

```bash
# Interactive mode
starmaker

# Or use subcommands directly
starmaker init          # Setup wizard
starmaker audit         # Audit your repo
starmaker draft         # Generate post drafts
starmaker post          # Publish drafts to platforms
starmaker auto-post     # Auto-generate & publish from README (NLP)
starmaker credentials   # Setup API keys
starmaker setup         # Browser-based credential wizard
starmaker awesome       # Find awesome-lists
starmaker compare       # Comparison table
starmaker readme        # README suggestions
starmaker all           # Run everything
```

## Setup

1. Clone this repo
2. Install dependencies:
   ```bash
   pip install -e ".[browser]"
   ```
3. Set up credentials (choose one method):

   **Option A: `.env` file (recommended)**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

   **Option B: Browser-based wizard**
   ```bash
   starmaker setup
   ```

   **Option C: Environment variables (CI/CD)**
   ```bash
   export DEVTO_API_KEY="your_key"
   export DISCORD_WEBHOOK_URLS="https://discord.com/api/webhooks/..."
   ```

4. Navigate to your project and run:
   ```bash
   starmaker init
   ```
5. Edit the generated `starmaker.yaml` to customize
6. Run `starmaker all` to generate everything

### Credential Loading Priority

Credentials are loaded from multiple sources with priority:

1. **Environment variables** (highest — for CI/CD)
2. **`.env` file** via python-dotenv (for local development)
3. **`~/.starmaker/credentials.yaml`** (legacy, backward compatible)

Non-empty values from higher-priority sources override lower ones.

## Commands

| Command | Description |
|---------|-------------|
| `starmaker init` | Interactive setup wizard — generates `starmaker.yaml` |
| `starmaker draft` | Generate post drafts for Reddit, HN, Dev.to, Twitter, Discord |
| `starmaker draft -p reddit` | Generate for a single platform |
| `starmaker auto-post` | Auto-generate posts from any README using NLP |
| `starmaker auto-post --readme path/to/README.md` | Specify README path |
| `starmaker auto-post --publish` | Generate and publish in one step |
| `starmaker auto-post --dry-run` | Preview generated posts |
| `starmaker auto-post -p devto` | Single platform |
| `starmaker audit` | Audit repo for star-worthiness (scores and suggestions) |
| `starmaker audit -u <url>` | Audit any GitHub repo by URL |
| `starmaker awesome` | Find matching awesome-lists and generate PR templates |
| `starmaker compare` | Generate feature comparison table vs competitors |
| `starmaker readme` | Analyze README and suggest enhancements |
| `starmaker post` | Publish drafts to platforms via official APIs |
| `starmaker post -p reddit` | Post to a single platform |
| `starmaker post --dry-run` | Preview what would be posted |
| `starmaker credentials` | View/setup API credentials with source info |
| `starmaker setup` | Browser-based credential setup wizard |
| `starmaker all` | Run all commands in sequence |

## Auto-Post (NLP-Powered)

Auto-generate platform-specific posts from any README.md — no LLM or external API needed.

```bash
# Generate drafts from a README
starmaker auto-post --readme /path/to/README.md --dry-run

# Generate and publish to all platforms
starmaker auto-post --readme /path/to/README.md --publish

# Single platform
starmaker auto-post --readme /path/to/README.md -p devto --publish
```

**How it works:**
- Parses README sections, extracts title, tagline, highlights, and tags
- Scores sentences by position and keyword frequency
- Infers technology tags (rust, python, react, etc.) automatically
- Maps tags to relevant subreddits
- Generates humanized, platform-specific drafts with randomized templates
- Output formats match each platform's content guidelines

**Supported platforms:**

| Platform | Post Type | Method |
|----------|-----------|--------|
| Reddit | Per-subreddit posts (auto-mapped from tags) | API |
| Dev.to | Full article with YAML frontmatter (saved as draft) | API |
| Twitter/X | 280-char tweet with hashtags | Browser intent |
| Discord | Webhook message with highlights | Webhook API |
| Hacker News | Show HN format with title + URL | Camoufox browser |

## Configuration

StarMaker uses a `starmaker.yaml` file. Run `starmaker init` to generate one, or copy `starmaker.example.yaml`.

```yaml
project:
  name: MyProject
  repo: https://github.com/user/my-project
  tagline: "One-line description"
  description: "Longer description..."
  competitors: [Alt1, Alt2]
  tags: [python, cli, open-source]
  highlights:
    - "Key feature 1"
    - "Key feature 2"
```

## Automated Credential Setup

StarMaker includes a browser-based setup wizard using Camoufox (anti-detection browser).

```bash
# Install browser automation (one-time)
pip install "starmaker-toolkit[browser]"

# Run the setup wizard
starmaker setup                # All platforms
starmaker setup -p reddit      # Single platform
starmaker setup --test-only    # Just test existing credentials
```

The wizard:
1. Opens a Camoufox browser window for each platform
2. You log in to your own account
3. The script creates API apps and extracts credentials automatically
4. Saves everything to `~/.starmaker/credentials.yaml`
5. Tests each credential to verify it works

No credentials are ever sent anywhere except to the official platform APIs.

## Publishing

StarMaker can publish drafts directly to platforms using their **official APIs**.

```bash
# 1. Setup credentials (one-time)
starmaker credentials      # Shows status and setup guides

# 2. Preview what will be posted
starmaker post --dry-run

# 3. Publish
starmaker post             # All platforms
starmaker post -p reddit   # Single platform
starmaker post -y          # Skip confirmation
```

### Platform API Requirements

| Platform | API Keys Needed | How to Get |
|----------|----------------|------------|
| Reddit | Client ID, Secret, Username, Password | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps/) (create "script" app) |
| Dev.to | API Key | [dev.to/settings/extensions](https://dev.to/settings/extensions) |
| Twitter/X | Optional (falls back to browser) | [developer.twitter.com](https://developer.twitter.com/) ($100/mo for API) |
| Discord | Webhook URL(s) | Server Settings > Integrations > Webhooks |
| Hacker News | None | Opens Camoufox browser with form auto-filled |

Credentials can be stored in:
- `.env` file (recommended) — copy `.env.example` to `.env`
- Environment variables (for CI/CD)
- `~/.starmaker/credentials.yaml` (legacy)

### Reddit Setup Guide

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps/)
2. Accept the [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564)
3. Scroll down and click **"create another app..."**
4. Fill in:
   - **name:** StarMaker (or any name)
   - **type:** Select **script**
   - **redirect uri:** `http://localhost:8080`
5. Click **"create app"**
6. Copy the **client ID** (string under the app name) and **secret**
7. Add to `.env`:
   ```
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_secret
   REDDIT_USERNAME=your_reddit_username
   REDDIT_PASSWORD=your_reddit_password
   ```

### Dev.to Setup Guide

1. Go to [dev.to/settings/extensions](https://dev.to/settings/extensions)
2. Under **DEV Community API Keys**, enter a description and click **Generate API Key**
3. Copy the key and add to `.env`:
   ```
   DEVTO_API_KEY=your_api_key
   ```
4. Articles are created as **drafts** by default — review on Dev.to before publishing

### Twitter/X Setup Guide

**Option A: Free (Browser Intent)**
No setup needed. StarMaker opens a pre-filled compose window in your default browser. Just click Tweet.

**Option B: API ($100/mo Basic plan)**
1. Go to [developer.twitter.com](https://developer.twitter.com/en/portal/dashboard)
2. Create a project and app
3. Generate API keys and access tokens
4. Add to `.env`:
   ```
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_SECRET=your_access_secret
   TWITTER_BEARER_TOKEN=your_bearer_token
   TWITTER_USERNAME=your_handle
   ```
5. Install the OAuth library: `pip install requests-oauthlib`

### Discord Setup Guide

1. Open your Discord server
2. Go to **Server Settings > Integrations > Webhooks**
3. Click **New Webhook**
4. Choose the channel (e.g., #showcase or #projects)
5. Copy the **Webhook URL**
6. Add to `.env`:
   ```
   DISCORD_WEBHOOK_URLS=https://discord.com/api/webhooks/...
   ```
7. For multiple channels, separate URLs with commas

### Hacker News

No API keys needed. StarMaker opens the HN submission page in Camoufox with the title and URL auto-filled. Log in and click Submit.

**Tip:** Post between 9-11 AM ET on weekdays for best visibility.

## Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests (100 tests)
pytest

# Run with coverage
pytest --cov=starmaker

# Lint
ruff check starmaker/ tests/
```

## How It Works

StarMaker uses **official platform APIs** with your own credentials. The NLP-based auto-post feature uses pure Python text processing (no LLM, no external NLP libraries) for README summarization.

- **Credential management**: Multi-source loading (env > .env > YAML) with file permission hardening
- **Browser automation**: Camoufox with anti-detection for platforms requiring browser interaction
- **Post generation**: Positional sentence scoring, keyword extraction, tag inference, and template-based humanization

## License

MIT
