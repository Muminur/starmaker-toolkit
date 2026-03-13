"""Automated Discord webhook setup.

Opens Discord in the browser, guides user to create a webhook,
and extracts the webhook URL.
"""

from __future__ import annotations

import time
import re

from rich.prompt import Prompt

from starmaker.setup_wizard.browser import launch_browser, wait_for_user_login
from starmaker.utils.console import console


def setup() -> dict[str, str] | None:
    """Run the Discord webhook setup wizard.

    Returns:
        Dict with discord_webhook_urls or None if setup failed.
    """
    console.print("\n[bold blue]Discord Webhook Setup[/bold blue]")
    console.print("This will help you create Discord webhooks for posting.\n")
    console.print("[bold]Note:[/bold] You need server admin/manage-webhooks permission.\n")

    webhook_urls = []

    with launch_browser(headless=False) as (browser, page):
        # Open Discord web
        page.goto("https://discord.com/login")
        time.sleep(2)

        # Wait for user to log in
        logged_in = wait_for_user_login(
            page,
            check_selector='[class*="guilds"], [data-list-id="guildsnav"]',
            platform="Discord",
            timeout=120,
        )

        if not logged_in:
            return None

        console.print("\n[bold yellow]Now, for each server/channel you want to post to:[/bold yellow]")
        console.print("1. Right-click the channel > Edit Channel")
        console.print("2. Go to Integrations > Webhooks")
        console.print("3. Click 'New Webhook' > 'Copy Webhook URL'\n")

        while True:
            url = Prompt.ask(
                "Paste webhook URL (or press Enter to finish)",
                default="",
            )
            if not url:
                break

            # Validate webhook URL format
            if re.match(r"https://discord\.com/api/webhooks/\d+/.+", url):
                webhook_urls.append(url)
                console.print(f"[green]Webhook added ({len(webhook_urls)} total)[/green]")
            else:
                console.print("[red]Invalid webhook URL format. Should start with https://discord.com/api/webhooks/[/red]")

    if webhook_urls:
        console.print(f"[green]{len(webhook_urls)} Discord webhook(s) collected![/green]")
        return {"discord_webhook_urls": ",".join(webhook_urls)}

    console.print("[red]Discord setup incomplete - no webhooks added.[/red]")
    return None
