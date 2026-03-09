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

## How It Works

StarMaker uses **official platform APIs** with your own credentials. It does not:
- Use browser automation or anti-detection tools
- Create fake engagement or artificial stars
- Violate any platform's terms of service

## License

MIT
