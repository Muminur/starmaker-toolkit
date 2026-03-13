# StarMaker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Universal OSS promotion toolkit. Generate promotional post drafts, audit your repo for star-worthiness, find awesome-lists, create comparison tables, and enhance your README — all without any AI or automation.

## Quick Start

```bash
# Install
pip install -e .

# Interactive mode
starmaker

# Or use subcommands directly
starmaker init          # Setup wizard
starmaker audit         # Audit your repo
starmaker draft         # Generate post drafts
starmaker post          # Publish drafts to platforms
starmaker credentials   # Setup API keys
starmaker awesome       # Find awesome-lists
starmaker compare       # Comparison table
starmaker readme        # README suggestions
starmaker all           # Run everything
```

## Setup

1. Clone this repo
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Navigate to your project and run:
   ```bash
   starmaker init
   ```
4. Edit the generated `starmaker.yaml` to customize
5. Run `starmaker all` to generate everything

## Commands

| Command | Description |
|---------|-------------|
| `starmaker init` | Interactive setup wizard — generates `starmaker.yaml` |
| `starmaker draft` | Generate post drafts for Reddit, HN, Dev.to, Twitter, Discord |
| `starmaker draft -p reddit` | Generate for a single platform |
| `starmaker audit` | Audit repo for star-worthiness (scores and suggestions) |
| `starmaker audit -u <url>` | Audit any GitHub repo by URL |
| `starmaker awesome` | Find matching awesome-lists and generate PR templates |
| `starmaker compare` | Generate feature comparison table vs competitors |
| `starmaker readme` | Analyze README and suggest enhancements |
| `starmaker post` | Publish drafts to platforms via official APIs |
| `starmaker post -p reddit` | Post to a single platform |
| `starmaker post --dry-run` | Preview what would be posted |
| `starmaker credentials` | View/setup API credentials |
| `starmaker all` | Run all commands in sequence |

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

StarMaker includes a browser-based setup wizard that automates API key creation.

```bash
# Install browser automation (one-time)
pip install "starmaker-toolkit[browser]"

# Run the setup wizard
starmaker setup                # All platforms
starmaker setup -p reddit      # Single platform
starmaker setup --test-only    # Just test existing credentials
```

The wizard:
1. Opens a browser window for each platform
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
# Edit ~/.starmaker/credentials.yaml with your API keys

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
| Hacker News | None | Opens browser with pre-filled form |

Credentials are stored in `~/.starmaker/credentials.yaml` (never committed to git).

### Reddit Setup Guide

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps/)
2. Scroll down and click **"create another app..."**
3. Fill in:
   - **name:** StarMaker (or any name)
   - **type:** Select **script**
   - **redirect uri:** `http://localhost:8080`
4. Click **"create app"**
5. Copy the **client ID** (string under the app name) and **secret**
6. Add to `~/.starmaker/credentials.yaml`:
   ```yaml
   reddit_client_id: "your_client_id"
   reddit_client_secret: "your_secret"
   reddit_username: "your_reddit_username"
   reddit_password: "your_reddit_password"
   ```

### Dev.to Setup Guide

1. Go to [dev.to/settings/extensions](https://dev.to/settings/extensions)
2. Under **DEV Community API Keys**, enter a description and click **Generate API Key**
3. Copy the key and add to `~/.starmaker/credentials.yaml`:
   ```yaml
   devto_api_key: "your_api_key"
   ```
4. Articles are created as **drafts** by default — review on Dev.to before publishing

### Twitter/X Setup Guide

**Option A: Free (Browser Intent)**
No setup needed. StarMaker opens a pre-filled compose window in your browser. Just click Tweet.

**Option B: API ($100/mo Basic plan)**
1. Go to [developer.twitter.com](https://developer.twitter.com/en/portal/dashboard)
2. Create a project and app
3. Generate API keys and access tokens
4. Add to `~/.starmaker/credentials.yaml`:
   ```yaml
   twitter_api_key: "your_api_key"
   twitter_api_secret: "your_api_secret"
   twitter_access_token: "your_access_token"
   twitter_access_secret: "your_access_secret"
   twitter_bearer_token: "your_bearer_token"
   twitter_username: "your_handle"
   ```
5. Install the OAuth library: `pip install requests-oauthlib`

### Discord Setup Guide

1. Open your Discord server
2. Go to **Server Settings > Integrations > Webhooks**
3. Click **New Webhook**
4. Choose the channel (e.g., #showcase or #projects)
5. Copy the **Webhook URL**
6. Add to `~/.starmaker/credentials.yaml`:
   ```yaml
   discord_webhook_urls: "https://discord.com/api/webhooks/..."
   ```
7. For multiple channels, separate URLs with commas:
   ```yaml
   discord_webhook_urls: "https://discord.com/api/webhooks/first,...,https://discord.com/api/webhooks/second,..."
   ```

### Hacker News

No setup needed. StarMaker opens the HN submission page in your browser with the title and URL pre-filled. Just log in and click Submit.

**Tip:** Post between 9-11 AM ET on weekdays for best visibility.

## How It Works

StarMaker uses **official platform APIs** with your own credentials. It does not:
- Use browser automation or anti-detection tools
- Create fake engagement or artificial stars
- Violate any platform's terms of service

## License

MIT
