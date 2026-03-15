"""StarMaker CLI — Universal OSS Promotion Toolkit."""

from __future__ import annotations

from pathlib import Path

import click
import yaml
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from starmaker import __version__
from starmaker.config import load_config, detect_local_repo
from starmaker.utils.console import console

BANNER = r"""
 ____  _             __  __       _
/ ___|| |_ __ _ _ __|  \/  | __ _| | _____ _ __
\___ \| __/ _` | '__| |\/| |/ _` | |/ / _ \ '__|
 ___) | || (_| | |  | |  | | (_| |   <  __/ |
|____/ \__\__,_|_|  |_|  |_|\__,_|_|\_\___|_|
"""


def _show_banner() -> None:
    console.print(Panel(
        f"[bold cyan]{BANNER}[/bold cyan]\n"
        f"[dim]v{__version__} — Universal OSS Promotion Toolkit[/dim]",
        border_style="cyan",
    ))


def _interactive_menu() -> None:
    """Show interactive menu when no subcommand given."""
    _show_banner()

    choices = {
        "1": ("init", "Initialize starmaker.yaml config"),
        "2": ("draft", "Generate promotional post drafts"),
        "3": ("post", "Publish drafts to platforms"),
        "4": ("audit", "Audit repo for star-worthiness"),
        "5": ("awesome", "Find awesome-lists & generate PRs"),
        "6": ("compare", "Generate comparison table"),
        "7": ("readme", "Analyze & enhance README"),
        "8": ("credentials", "View API credential status"),
        "9": ("setup", "Auto-setup credentials (browser wizard)"),
        "0": ("all", "Run everything"),
        "q": ("quit", "Exit"),
    }

    console.print("\n[bold]What would you like to do?[/bold]\n")
    for key, (cmd, desc) in choices.items():
        console.print(f"  [cyan]{key}[/cyan]) {desc}")

    choice = Prompt.ask("\nSelect", choices=list(choices.keys()), default="7")

    if choice == "q":
        return

    cmd = choices[choice][0]
    ctx = click.Context(cli)
    ctx.invoke(globals().get(f"cmd_{cmd}", cmd_all))


@click.group(invoke_without_command=True)
@click.version_option(__version__)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """StarMaker — Universal OSS Promotion Toolkit.

    Generate promotional content, audit your repo, find awesome-lists,
    and enhance your README to attract more stars.

    Run without arguments for interactive mode.
    """
    if ctx.invoked_subcommand is None:
        _interactive_menu()


@cli.command("init")
def cmd_init() -> None:
    """Initialize starmaker.yaml configuration."""
    config_path = Path("starmaker.yaml")
    if config_path.exists():
        if not Confirm.ask("[yellow]starmaker.yaml already exists. Overwrite?[/yellow]"):
            return

    console.print("\n[bold blue]StarMaker Setup Wizard[/bold blue]\n")

    # Try to detect from local repo
    local = detect_local_repo()

    name = Prompt.ask("Project name", default=local.get("name", ""))
    repo = Prompt.ask("GitHub repo URL", default=local.get("repo", ""))
    tagline = Prompt.ask("One-line tagline")
    description = Prompt.ask("Description (2-3 sentences)")

    competitors_raw = Prompt.ask("Competitors (comma-separated)", default="")
    competitors = [c.strip() for c in competitors_raw.split(",") if c.strip()]

    tags_raw = Prompt.ask("Tags/topics (comma-separated)", default="")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    highlights_list = []
    console.print("\n[dim]Enter key highlights (empty line to finish):[/dim]")
    while True:
        h = Prompt.ask("  Highlight", default="")
        if not h:
            break
        highlights_list.append(h)

    author_name = Prompt.ask("\nYour name", default="")
    github_user = Prompt.ask("GitHub username", default=local.get("owner", ""))
    twitter = Prompt.ask("Twitter/X handle (optional)", default="")

    subreddits_raw = Prompt.ask(
        "Target subreddits (comma-separated)",
        default="opensource, commandline, programming",
    )
    subreddits = [s.strip() for s in subreddits_raw.split(",") if s.strip()]

    config_data = {
        "project": {
            "name": name,
            "repo": repo,
            "tagline": tagline,
            "description": description,
            "website": "",
            "competitors": competitors,
            "tags": tags,
            "highlights": highlights_list,
            "tech_stack": [],
        },
        "author": {
            "name": author_name,
            "github": github_user,
            "twitter": twitter,
            "website": "",
        },
        "promotion": {
            "platforms": ["reddit", "hackernews", "devto", "twitter", "discord"],
            "reddit": {"subreddits": subreddits},
            "awesome_lists": [],
            "comparison": {"features": [], "competitors": {}},
        },
    }

    with open(config_path, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    console.print(Panel(
        f"[bold green]Config saved to {config_path}[/bold green]\n\n"
        "Edit the file to add more details, then run:\n"
        "  [cyan]starmaker draft[/cyan]  — Generate post drafts\n"
        "  [cyan]starmaker audit[/cyan]  — Audit your repo\n"
        "  [cyan]starmaker all[/cyan]    — Run everything",
        title="Setup Complete",
        border_style="green",
    ))


@cli.command("draft")
@click.option("--platform", "-p", help="Generate for a specific platform only")
@click.option("--output", "-o", default="drafts", help="Output directory")
def cmd_draft(platform: str | None, output: str) -> None:
    """Generate promotional post drafts for all platforms."""
    from starmaker.commands.draft_posts import run
    config = load_config()
    run(config, platform=platform, output_dir=output)


@cli.command("post")
@click.option("--platform", "-p", help="Post to a specific platform only")
@click.option("--drafts", "-d", "drafts_dir", default="drafts", help="Drafts directory")
@click.option("--dry-run", is_flag=True, help="Preview posts without publishing")
@click.option("--yes", "-y", "skip_confirm", is_flag=True, help="Skip confirmation prompt")
def cmd_post(platform: str | None, drafts_dir: str, dry_run: bool, skip_confirm: bool) -> None:
    """Publish drafts to platforms via official APIs."""
    from starmaker.commands.post import run
    config = load_config()
    run(config, platform=platform, drafts_dir=drafts_dir, dry_run=dry_run, skip_confirm=skip_confirm)


@cli.command("credentials")
def cmd_credentials() -> None:
    """View API credential status and sources."""
    from starmaker.credentials import (
        init_credentials, load_credentials, get_credential_sources,
        CREDENTIALS_DIR,
    )

    init_credentials()
    creds = load_credentials()
    sources = get_credential_sources()

    console.print(Panel(
        f"[bold]Credentials directory:[/bold] {CREDENTIALS_DIR}\n"
        f"[bold]Supported sources:[/bold] env vars > .env file > credentials.yaml\n",
        title="StarMaker Credentials",
        border_style="blue",
    ))

    platform_keys = {
        "Reddit": ["reddit_client_id", "reddit_client_secret", "reddit_username", "reddit_password"],
        "Dev.to": ["devto_api_key"],
        "Twitter/X": ["twitter_api_key", "twitter_api_secret", "twitter_access_token",
                       "twitter_access_secret", "twitter_bearer_token", "twitter_username"],
        "Discord": ["discord_webhook_urls"],
        "Hacker News": [],
    }

    from rich.table import Table
    table = Table(title="Credential Status", border_style="blue")
    table.add_column("Platform", style="bold")
    table.add_column("Status")
    table.add_column("Source")
    table.add_column("Setup Guide")

    source_styles = {
        "env": "[green]env var[/green]",
        "dotenv": "[cyan].env file[/cyan]",
        "yaml": "[yellow]yaml file[/yellow]",
        "unset": "[dim]not set[/dim]",
    }

    for platform_name, keys in platform_keys.items():
        if not keys:
            table.add_row(platform_name, "[green]No keys needed[/green]", "", "Opens browser")
            continue

        configured = sum(1 for k in keys if creds.get(k))
        total = len(keys)

        if configured == total:
            # Show the source of the first key as representative
            src = sources.get(keys[0], "unset")
            table.add_row(
                platform_name,
                "[green]Configured[/green]",
                source_styles.get(src, src),
                "",
            )
        else:
            # Show mixed sources
            src_summary = set(sources.get(k, "unset") for k in keys if creds.get(k))
            src_text = ", ".join(source_styles.get(s, s) for s in src_summary) if src_summary else source_styles["unset"]

            guides = {
                "Reddit": "https://www.reddit.com/prefs/apps/",
                "Dev.to": "https://dev.to/settings/extensions",
                "Twitter/X": "https://developer.twitter.com/",
                "Discord": "Server Settings > Webhooks",
            }
            table.add_row(
                platform_name,
                f"[yellow]{configured}/{total} keys[/yellow]",
                src_text,
                guides.get(platform_name, ""),
            )

    console.print(table)

    console.print("\n[dim]Options for setting credentials:[/dim]")
    console.print("  [cyan]1.[/cyan] Set environment variables (e.g. REDDIT_CLIENT_ID)")
    console.print("  [cyan]2.[/cyan] Create a .env file (copy from .env.example)")
    console.print(f"  [cyan]3.[/cyan] Edit {CREDENTIALS_DIR / 'credentials.yaml'}")
    console.print("  [cyan]4.[/cyan] Run [cyan]starmaker setup[/cyan] for browser-based setup")


@cli.command("setup")
@click.option("--platform", "-p", multiple=True, help="Platform(s) to set up (reddit, devto, discord)")
@click.option("--test-only", is_flag=True, help="Only test existing credentials")
def cmd_setup(platform: tuple[str, ...], test_only: bool) -> None:
    """Automated credential setup wizard (opens browser)."""
    from starmaker.setup_wizard.wizard import run_wizard, test_all_credentials
    from starmaker.credentials import load_credentials

    if test_only:
        test_all_credentials(load_credentials())
    else:
        platforms = list(platform) if platform else None
        run_wizard(platforms=platforms)


@cli.command("audit")
@click.option("--url", "-u", help="GitHub repo URL (auto-detects from local repo if omitted)")
def cmd_audit(url: str | None) -> None:
    """Audit a repository for star-worthiness."""
    from starmaker.commands.audit import run
    run(repo_url=url)


@cli.command("awesome")
@click.option("--output", "-o", default="drafts", help="Output directory")
def cmd_awesome(output: str) -> None:
    """Find awesome-lists and generate PR content."""
    from starmaker.commands.awesome import run
    config = load_config()
    run(config, output_dir=output)


@cli.command("compare")
@click.option("--output", "-o", default="drafts", help="Output directory")
def cmd_compare(output: str) -> None:
    """Generate feature comparison table."""
    from starmaker.commands.compare import run
    config = load_config()
    run(config, output_dir=output)


@cli.command("readme")
@click.option("--file", "-f", "readme_path", help="Path to README file")
@click.option("--output", "-o", default="drafts", help="Output directory")
def cmd_readme(readme_path: str | None, output: str) -> None:
    """Analyze README and suggest enhancements."""
    from starmaker.commands.readme import run
    config = load_config()
    run(config, readme_path=readme_path, output_dir=output)


@cli.command("all")
@click.option("--output", "-o", default="drafts", help="Output directory")
@click.option("--url", "-u", help="GitHub repo URL for audit")
def cmd_all(output: str, url: str | None) -> None:
    """Run all commands: audit, drafts, awesome-lists, comparison, README."""
    config = load_config()

    console.print(Panel("[bold cyan]Running full StarMaker suite...[/bold cyan]", border_style="cyan"))

    # 1. Audit
    console.rule("[bold]1/5 — Repository Audit[/bold]")
    from starmaker.commands.audit import run as run_audit
    run_audit(repo_url=url)

    # 2. Draft posts
    console.rule("[bold]2/5 — Post Drafts[/bold]")
    from starmaker.commands.draft_posts import run as run_draft
    run_draft(config, output_dir=output)

    # 3. Awesome lists
    console.rule("[bold]3/5 — Awesome Lists[/bold]")
    from starmaker.commands.awesome import run as run_awesome
    run_awesome(config, output_dir=output)

    # 4. Comparison
    console.rule("[bold]4/5 — Comparison Table[/bold]")
    from starmaker.commands.compare import run as run_compare
    run_compare(config, output_dir=output)

    # 5. README
    console.rule("[bold]5/5 — README Analysis[/bold]")
    from starmaker.commands.readme import run as run_readme
    run_readme(config, output_dir=output)

    console.print(Panel(
        f"[bold green]All done! Check ./{output}/ for generated content.[/bold green]\n\n"
        "Next steps:\n"
        "1. Review and customize each draft\n"
        "2. Run [cyan]starmaker post[/cyan] to publish drafts\n"
        "3. Submit PRs to awesome-lists\n"
        "4. Update your README with suggestions",
        title="StarMaker Complete",
        border_style="green",
    ))


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
