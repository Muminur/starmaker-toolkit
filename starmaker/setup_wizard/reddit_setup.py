"""Automated Reddit API credential setup.

Creates a Reddit "script" app and extracts client_id and client_secret.
User logs in manually, then the script handles the rest.
"""

from __future__ import annotations

import time
import uuid

from rich.prompt import Prompt

from starmaker.setup_wizard.browser import (
    launch_browser,
    wait_for_user_login,
    safe_click,
    safe_fill,
    safe_get_text,
)
from starmaker.utils.console import console


def setup() -> dict[str, str] | None:
    """Run the Reddit credential setup wizard.

    Returns:
        Dict with reddit_client_id, reddit_client_secret, reddit_username, reddit_password
        or None if setup failed.
    """
    console.print("\n[bold blue]Reddit API Setup[/bold blue]")
    console.print("This will create a Reddit 'script' app to get API credentials.\n")

    # Get username/password upfront (needed for OAuth script flow)
    reddit_username = Prompt.ask("Reddit username")
    reddit_password = Prompt.ask("Reddit password", password=True)

    console.print("\n[dim]Opening browser for Reddit login...[/dim]")

    with launch_browser(headless=False) as (browser, page):
        # Navigate to Reddit login
        page.goto("https://www.reddit.com/login/")
        time.sleep(2)

        # Wait for user to log in
        logged_in = wait_for_user_login(
            page,
            check_selector='a[href*="/user/"], button[id*="USER_DROPDOWN"]',
            platform="Reddit",
            timeout=120,
        )

        if not logged_in:
            return None

        # Navigate to app creation page
        console.print("[dim]Navigating to app creation page...[/dim]")
        page.goto("https://www.reddit.com/prefs/apps/")
        time.sleep(3)

        # Scroll to bottom and click "create another app" or "create an app"
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)

        # Try clicking the create button
        create_clicked = safe_click(page, 'button:has-text("create another app")', timeout=3000)
        if not create_clicked:
            create_clicked = safe_click(page, 'button:has-text("create an app")', timeout=3000)
        if not create_clicked:
            # Try link-styled button
            create_clicked = safe_click(page, 'a:has-text("create another app")', timeout=3000)
        if not create_clicked:
            create_clicked = safe_click(page, 'a:has-text("create an app")', timeout=3000)

        if not create_clicked:
            console.print("[yellow]Could not find create app button. Trying form directly...[/yellow]")

        time.sleep(2)

        # Fill in the app creation form
        app_name = f"starmaker-{uuid.uuid4().hex[:6]}"

        # Name field
        safe_fill(page, 'input[name="app_name"], #app_name', app_name)

        # Select "script" type
        script_radio = page.query_selector('input[type="radio"][value="script"]')
        if script_radio:
            script_radio.click()
        else:
            # Try label click
            safe_click(page, 'label:has-text("script")', timeout=3000)

        time.sleep(1)

        # Description (optional)
        safe_fill(page, 'textarea[name="app_description"], #app_description', "StarMaker OSS promotion toolkit")

        # About URL (optional)
        safe_fill(page, 'input[name="about_url"], #about_url', "https://github.com/Muminur/starmaker-toolkit")

        # Redirect URI (required for script apps)
        safe_fill(page, 'input[name="redirect_uri"], #redirect_uri', "http://localhost:8080")

        time.sleep(1)

        # Submit the form
        submit_clicked = safe_click(page, 'button:has-text("create app")', timeout=3000)
        if not submit_clicked:
            submit_clicked = safe_click(page, 'input[type="submit"][value*="create"]', timeout=3000)

        if not submit_clicked:
            console.print("[yellow]Please click 'create app' in the browser.[/yellow]")
            console.print("[dim]Waiting up to 30 seconds...[/dim]")
            time.sleep(30)

        time.sleep(3)

        # Extract credentials from the page
        # After creating, the page shows the app with client_id and secret
        page.goto("https://www.reddit.com/prefs/apps/")
        time.sleep(3)

        # The client ID is shown under the app name as a small code block
        # The secret is shown next to "secret"
        page_content = page.content()

        client_id = ""
        client_secret = ""

        # Try to find app entries - Reddit shows them in a specific structure
        app_listings = page.query_selector_all('.app-listing, .developed-app, [data-app-id]')

        if app_listings:
            for app in app_listings:
                text = app.text_content() or ""
                if app_name in text or "starmaker" in text.lower():
                    # Extract client_id - usually a short string shown below the name
                    # And secret - shown next to "secret" label
                    inner_html = app.inner_html()

                    # Look for the ID pattern (alphanumeric, typically 14+ chars)
                    import re
                    id_matches = re.findall(r'<code[^>]*>([A-Za-z0-9_-]{10,30})</code>', inner_html)
                    if id_matches:
                        client_id = id_matches[0]

                    secret_matches = re.findall(r'secret[^<]*</[^>]+>\s*([A-Za-z0-9_-]{20,50})', inner_html, re.IGNORECASE)
                    if secret_matches:
                        client_secret = secret_matches[0]
                    break

        # If automated extraction failed, ask user to copy
        if not client_id or not client_secret:
            console.print("\n[yellow]Could not auto-extract credentials from page.[/yellow]")
            console.print("The app should be visible on the page. Look for:")
            console.print("  - Client ID: short string under the app name")
            console.print("  - Secret: shown next to 'secret' label\n")

            client_id = Prompt.ask("Paste the Client ID (string under app name)")
            client_secret = Prompt.ask("Paste the Secret")

    if client_id and client_secret:
        credentials = {
            "reddit_client_id": client_id,
            "reddit_client_secret": client_secret,
            "reddit_username": reddit_username,
            "reddit_password": reddit_password,
        }
        console.print("[green]Reddit credentials collected![/green]")
        return credentials

    console.print("[red]Reddit setup incomplete.[/red]")
    return None
