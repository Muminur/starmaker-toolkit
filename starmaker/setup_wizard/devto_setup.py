"""Automated Dev.to API key setup.

Navigates to Dev.to settings, user logs in, then generates an API key.
"""

from __future__ import annotations

import time

from rich.prompt import Prompt

from starmaker.setup_wizard.browser import (
    launch_browser,
    wait_for_user_login,
    safe_click,
    safe_fill,
    safe_get_value,
)
from starmaker.utils.console import console


def setup() -> dict[str, str] | None:
    """Run the Dev.to credential setup wizard.

    Returns:
        Dict with devto_api_key or None if setup failed.
    """
    console.print("\n[bold blue]Dev.to API Setup[/bold blue]")
    console.print("This will generate a Dev.to API key for publishing articles.\n")

    with launch_browser(headless=False) as (browser, page):
        # Navigate to Dev.to login
        page.goto("https://dev.to/enter")
        time.sleep(2)

        # Wait for user to log in
        logged_in = wait_for_user_login(
            page,
            check_selector='a[href="/notifications"], img.crayons-avatar',
            platform="Dev.to",
            timeout=120,
        )

        if not logged_in:
            return None

        # Navigate to API settings
        console.print("[dim]Navigating to API key settings...[/dim]")
        page.goto("https://dev.to/settings/extensions")
        time.sleep(3)

        # Scroll to the API Keys section
        page.evaluate("""
            const heading = document.querySelector('h2, h3');
            const elements = document.querySelectorAll('h2, h3');
            for (const el of elements) {
                if (el.textContent.includes('API') || el.textContent.includes('DEV')) {
                    el.scrollIntoView();
                    break;
                }
            }
        """)
        time.sleep(1)

        # Fill in the description field for the new key
        description_filled = safe_fill(
            page,
            'input[placeholder*="API Key Description"], input[name*="description"], #new_key_description',
            "StarMaker Toolkit",
        )

        if not description_filled:
            # Try finding any text input near "Generate" button
            inputs = page.query_selector_all('input[type="text"]')
            for inp in inputs:
                parent = inp.evaluate_handle("el => el.closest('form') || el.parentElement")
                parent_text = parent.evaluate("el => el.textContent") if parent else ""
                if "api" in parent_text.lower() or "key" in parent_text.lower():
                    inp.fill("StarMaker Toolkit")
                    description_filled = True
                    break

        time.sleep(1)

        # Click "Generate API Key" button
        generate_clicked = safe_click(page, 'button:has-text("Generate API Key")', timeout=3000)
        if not generate_clicked:
            generate_clicked = safe_click(page, 'input[type="submit"][value*="Generate"]', timeout=3000)
        if not generate_clicked:
            generate_clicked = safe_click(page, 'button:has-text("Generate")', timeout=3000)

        if not generate_clicked:
            console.print("[yellow]Please click 'Generate API Key' in the browser.[/yellow]")
            time.sleep(15)

        time.sleep(3)

        # Try to extract the generated key
        # Dev.to typically shows it in a code block or input after generation
        api_key = ""

        # Check for key display - it's usually shown once after generation
        key_elements = page.query_selector_all('code, .api-key, input[readonly], [data-copy-text]')
        for el in key_elements:
            text = el.text_content() or el.get_attribute("value") or el.get_attribute("data-copy-text") or ""
            # Dev.to API keys are typically 24+ alphanumeric chars
            text = text.strip()
            if len(text) >= 20 and text.isalnum():
                api_key = text
                break

        # If not found, check for copy buttons or visible key text
        if not api_key:
            # Look for newly appeared elements
            page.wait_for_timeout(2000)
            all_text = page.content()
            import re
            # Dev.to keys look like: a long alphanumeric string
            matches = re.findall(r'value="([A-Za-z0-9]{20,60})"', all_text)
            if matches:
                api_key = matches[-1]  # Last one is likely the new key

        if not api_key:
            console.print("\n[yellow]Could not auto-extract the API key.[/yellow]")
            console.print("The key should be visible on the page. Copy it.\n")
            api_key = Prompt.ask("Paste your Dev.to API key")

    if api_key:
        console.print("[green]Dev.to API key collected![/green]")
        return {"devto_api_key": api_key}

    console.print("[red]Dev.to setup incomplete.[/red]")
    return None
