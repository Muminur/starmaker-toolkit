"""Main setup wizard that orchestrates all platform credential setups."""

from __future__ import annotations

import requests
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from starmaker.credentials import load_credentials, save_credentials, init_credentials
from starmaker.utils.console import console


def _test_reddit(credentials: dict[str, str]) -> tuple[bool, str]:
    """Test Reddit credentials by requesting an access token."""
    try:
        auth = (credentials["reddit_client_id"], credentials["reddit_client_secret"])
        data = {
            "grant_type": "password",
            "username": credentials["reddit_username"],
            "password": credentials["reddit_password"],
        }
        headers = {"User-Agent": f"StarMaker/0.2.0 (by /u/{credentials['reddit_username']})"}

        resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth, data=data, headers=headers, timeout=10,
        )

        if resp.status_code == 200:
            token_data = resp.json()
            if "access_token" in token_data:
                return True, f"Authenticated as u/{credentials['reddit_username']}"
            return False, f"Auth failed: {token_data.get('error', 'unknown')}"
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)


def _test_devto(credentials: dict[str, str]) -> tuple[bool, str]:
    """Test Dev.to API key by fetching user profile."""
    try:
        resp = requests.get(
            "https://dev.to/api/users/me",
            headers={"api-key": credentials["devto_api_key"]},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return True, f"Authenticated as @{data.get('username', 'unknown')}"
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)


def _test_discord(credentials: dict[str, str]) -> tuple[bool, str]:
    """Test Discord webhook URLs by sending a GET request."""
    urls = [u.strip() for u in credentials.get("discord_webhook_urls", "").split(",") if u.strip()]
    if not urls:
        return False, "No webhook URLs configured"

    results = []
    for i, url in enumerate(urls):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                channel = data.get("channel_id", "?")
                results.append(f"Webhook {i + 1}: OK (channel {channel})")
            else:
                results.append(f"Webhook {i + 1}: HTTP {resp.status_code}")
        except Exception as e:
            results.append(f"Webhook {i + 1}: Error - {e}")

    ok_count = sum(1 for r in results if "OK" in r)
    return ok_count > 0, "; ".join(results)


def test_all_credentials(credentials: dict[str, str]) -> None:
    """Test all configured credentials."""
    console.print("\n[bold blue]Testing credentials...[/bold blue]\n")

    table = Table(title="Credential Tests", border_style="blue")
    table.add_column("Platform", style="bold")
    table.add_column("Status")
    table.add_column("Details")

    # Reddit
    if credentials.get("reddit_client_id"):
        ok, msg = _test_reddit(credentials)
        table.add_row("Reddit", "[green]PASS[/green]" if ok else "[red]FAIL[/red]", msg)
    else:
        table.add_row("Reddit", "[dim]Skipped[/dim]", "No credentials configured")

    # Dev.to
    if credentials.get("devto_api_key"):
        ok, msg = _test_devto(credentials)
        table.add_row("Dev.to", "[green]PASS[/green]" if ok else "[red]FAIL[/red]", msg)
    else:
        table.add_row("Dev.to", "[dim]Skipped[/dim]", "No credentials configured")

    # Discord
    if credentials.get("discord_webhook_urls"):
        ok, msg = _test_discord(credentials)
        table.add_row("Discord", "[green]PASS[/green]" if ok else "[red]FAIL[/red]", msg)
    else:
        table.add_row("Discord", "[dim]Skipped[/dim]", "No credentials configured")

    # Twitter/X (browser intent, always works)
    table.add_row("Twitter/X", "[green]PASS[/green]", "Uses free browser intent (no API needed)")

    # Hacker News (browser, always works)
    table.add_row("Hacker News", "[green]PASS[/green]", "Opens browser (no API needed)")

    console.print(table)


def run_wizard(platforms: list[str] | None = None) -> None:
    """Run the interactive credential setup wizard.

    Args:
        platforms: List of platforms to set up. If None, asks user.
    """
    init_credentials()
    credentials = load_credentials()

    console.print(Panel(
        "[bold cyan]StarMaker Credential Setup Wizard[/bold cyan]\n\n"
        "This wizard will open a browser for each platform.\n"
        "You log in to your own account, and the script\n"
        "creates API keys and saves them automatically.",
        border_style="cyan",
    ))

    available = {
        "reddit": ("Reddit", "reddit_client_id"),
        "devto": ("Dev.to", "devto_api_key"),
        "discord": ("Discord", "discord_webhook_urls"),
    }

    # Show current status
    table = Table(title="Current Status", border_style="blue")
    table.add_column("Platform", style="bold")
    table.add_column("Status")

    for key, (name, check_key) in available.items():
        configured = bool(credentials.get(check_key))
        table.add_row(name, "[green]Configured[/green]" if configured else "[yellow]Not set up[/yellow]")

    table.add_row("Twitter/X", "[green]No setup needed[/green] (browser intent)")
    table.add_row("Hacker News", "[green]No setup needed[/green] (browser)")
    console.print(table)

    # Determine which to set up
    if platforms is None:
        platforms_to_setup = []
        for key, (name, check_key) in available.items():
            configured = bool(credentials.get(check_key))
            default = not configured
            if Confirm.ask(f"\nSet up {name}?", default=default):
                platforms_to_setup.append(key)
    else:
        platforms_to_setup = [p for p in platforms if p in available]

    if not platforms_to_setup:
        console.print("\n[dim]No platforms selected. Exiting wizard.[/dim]")
        return

    # Run each platform setup
    for plat in platforms_to_setup:
        try:
            if plat == "reddit":
                from starmaker.setup_wizard.reddit_setup import setup
                result = setup()
            elif plat == "devto":
                from starmaker.setup_wizard.devto_setup import setup
                result = setup()
            elif plat == "discord":
                from starmaker.setup_wizard.discord_setup import setup
                result = setup()
            else:
                continue

            if result:
                credentials.update(result)
                save_credentials(credentials)
                console.print(f"[green]Saved {available[plat][0]} credentials to YAML.[/green]")
                console.print("[dim]Tip: You can also set these as environment variables or in a .env file.[/dim]\n")
            else:
                console.print(f"[yellow]Skipped {available[plat][0]}.[/yellow]\n")

        except Exception as e:
            console.print(f"[red]Error setting up {available[plat][0]}: {e}[/red]\n")

    # Test all credentials
    if Confirm.ask("\n[bold]Test all credentials now?[/bold]", default=True):
        test_all_credentials(credentials)

    console.print(Panel(
        "[bold green]Setup complete![/bold green]\n\n"
        "Credentials saved to ~/.starmaker/credentials.yaml\n"
        "You can also use a .env file or environment variables.\n\n"
        "Run [cyan]starmaker post --dry-run[/cyan] to preview posts.\n"
        "Run [cyan]starmaker post[/cyan] to publish.",
        title="Done",
        border_style="green",
    ))
