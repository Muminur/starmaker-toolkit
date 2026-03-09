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

## How It Works

StarMaker generates **text content** for you to post manually. It does not:
- Automate posting to any platform
- Create fake engagement
- Violate any platform's terms of service

It's a content generator and repo auditor — you do the posting.

## License

MIT
