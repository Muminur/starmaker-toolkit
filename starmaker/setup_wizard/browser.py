"""Shared browser utilities for the setup wizard."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator

from camoufox.sync_api import Camoufox
from playwright.sync_api import Page, BrowserContext

from starmaker.utils.console import console


@contextmanager
def launch_browser(headless: bool = False) -> Generator[tuple[BrowserContext, Page], None, None]:
    """Launch a Camoufox browser instance.

    Args:
        headless: Run without visible window (default: False for user login).

    Yields:
        Tuple of (browser_context, page).
    """
    with Camoufox(headless=headless) as browser:
        page = browser.new_page()
        yield browser, page


def wait_for_user_login(page: Page, check_selector: str, platform: str, timeout: int = 120) -> bool:
    """Wait for user to complete login on a platform.

    Args:
        page: Playwright page.
        check_selector: CSS selector that appears when logged in.
        platform: Platform name for display.
        timeout: Max seconds to wait.

    Returns:
        True if login detected, False if timeout.
    """
    console.print(f"\n[bold yellow]Please log in to {platform} in the browser window.[/bold yellow]")
    console.print(f"[dim]Waiting up to {timeout} seconds...[/dim]\n")

    start = time.time()
    while time.time() - start < timeout:
        try:
            if page.query_selector(check_selector):
                console.print(f"[green]Logged in to {platform}![/green]")
                return True
        except Exception:
            pass
        time.sleep(2)

    console.print(f"[red]Timed out waiting for {platform} login.[/red]")
    return False


def safe_click(page: Page, selector: str, timeout: int = 5000) -> bool:
    """Safely click an element, returning False if not found."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.click(selector)
        return True
    except Exception:
        return False


def safe_fill(page: Page, selector: str, value: str, timeout: int = 5000) -> bool:
    """Safely fill an input field."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.fill(selector, value)
        return True
    except Exception:
        return False


def safe_get_text(page: Page, selector: str, timeout: int = 5000) -> str:
    """Safely get text content of an element."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        element = page.query_selector(selector)
        if element:
            return element.text_content() or ""
    except Exception:
        pass
    return ""


def safe_get_value(page: Page, selector: str, timeout: int = 5000) -> str:
    """Safely get the value of an input field."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        element = page.query_selector(selector)
        if element:
            return element.input_value() or element.get_attribute("value") or ""
    except Exception:
        pass
    return ""
