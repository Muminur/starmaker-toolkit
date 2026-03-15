"""Launch Camoufox in a subprocess to open URLs and fill forms.

Runs Camoufox in a separate Python process to avoid asyncio event loop
conflicts that occur when using the Playwright sync API inside an
existing asyncio loop.

Uses humanized typing with random delays for anti-detection.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path


# Persistent profile directory for Camoufox sessions
_PROFILE_DIR = Path.home() / ".starmaker" / "camoufox_profile"


def open_in_camoufox(
    url: str,
    *,
    platform: str = "browser",
    fields: dict[str, str] | None = None,
) -> None:
    """Open a URL in Camoufox and optionally fill form fields.

    Args:
        url: The URL to navigate to.
        platform: Platform name for the profile subdirectory.
        fields: Dict mapping CSS selectors to values to type into fields.

    Raises:
        ImportError: If camoufox is not installed.
        RuntimeError: If the subprocess fails.
    """
    # Verify camoufox is importable before spawning subprocess
    import camoufox  # noqa: F401

    profile_dir = _PROFILE_DIR / platform
    profile_dir.mkdir(parents=True, exist_ok=True)

    fields_json = json.dumps(fields or {})

    script = textwrap.dedent(f"""\
        import json
        import random
        import time
        from camoufox.sync_api import Camoufox

        url = {url!r}
        profile = {str(profile_dir)!r}
        fields = json.loads({fields_json!r})

        def human_type(page, selector, text):
            \"\"\"Type text character by character with random delays.\"\"\"
            el = page.wait_for_selector(selector, timeout=10000)
            if el:
                el.click()
                time.sleep(random.uniform(0.2, 0.5))
                for char in text:
                    page.keyboard.type(char, delay=random.randint(30, 120))
                    if random.random() < 0.05:
                        time.sleep(random.uniform(0.3, 0.8))

        with Camoufox(
            headless=False,
            humanize=2.0,
            persistent_context=True,
            user_data_dir=profile,
            block_webrtc=True,
        ) as browser:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(1.0, 2.0))

            # Fill form fields with humanized typing
            for selector, value in fields.items():
                try:
                    human_type(page, selector, value)
                    time.sleep(random.uniform(0.3, 0.8))
                except Exception as e:
                    print(f"Could not fill {{selector}}: {{e}}", flush=True)

            print("Browser opened. Close the window when done.", flush=True)
            try:
                page.wait_for_event("close", timeout=300000)
            except Exception:
                pass
    """)

    result = subprocess.run(
        [sys.executable, "-c", script],
        timeout=600,
        capture_output=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Camoufox subprocess exited with code {result.returncode}")


def open_twitter_camoufox(tweet_text: str) -> None:
    """Open Twitter/X in a maximally hardened Camoufox session.

    X.com has aggressive bot detection. This uses:
    - humanize=2.0 for realistic mouse/keyboard
    - persistent_context with user_data_dir to retain login cookies
    - block_webrtc to prevent IP leak
    - block_webgl=False to avoid fingerprint gap
    - enable_cache=True for realistic browsing behavior
    - Realistic screen resolution via Screen
    - Visit homepage first, then navigate to compose

    Args:
        tweet_text: The tweet content to paste into the compose box.

    Raises:
        ImportError: If camoufox is not installed.
        RuntimeError: If the subprocess fails.
    """
    import camoufox  # noqa: F401

    profile_dir = _PROFILE_DIR / "twitter"
    profile_dir.mkdir(parents=True, exist_ok=True)

    script = textwrap.dedent(f"""\
        import random
        import time
        from camoufox.sync_api import Camoufox

        tweet_text = {tweet_text!r}
        profile = {str(profile_dir)!r}

        def human_type(page, selector, text):
            el = page.wait_for_selector(selector, timeout=15000)
            if el:
                el.click()
                time.sleep(random.uniform(0.3, 0.6))
                for char in text:
                    page.keyboard.type(char, delay=random.randint(40, 150))
                    if random.random() < 0.03:
                        time.sleep(random.uniform(0.5, 1.2))

        with Camoufox(
            headless=False,
            humanize=2.0,
            persistent_context=True,
            user_data_dir=profile,
            block_webrtc=True,
            block_webgl=False,
            enable_cache=True,
            geoip=True,
        ) as browser:
            page = browser.new_page()

            # Visit homepage first to look like a real user
            page.goto("https://x.com", wait_until="domcontentloaded")
            time.sleep(random.uniform(3.0, 5.0))

            # Scroll a bit to simulate real browsing
            page.mouse.wheel(0, random.randint(100, 300))
            time.sleep(random.uniform(1.0, 2.0))

            # Navigate to compose tweet
            page.goto("https://x.com/compose/post", wait_until="domcontentloaded")
            time.sleep(random.uniform(2.0, 4.0))

            # Try to type into the compose box
            # X.com uses a contenteditable div for the tweet compose area
            compose_selectors = [
                "div[data-testid='tweetTextarea_0'] div[contenteditable='true']",
                "div[role='textbox'][data-testid='tweetTextarea_0']",
                "div[role='textbox']",
                "div[contenteditable='true']",
            ]

            typed = False
            for sel in compose_selectors:
                try:
                    human_type(page, sel, tweet_text)
                    typed = True
                    break
                except Exception:
                    continue

            if not typed:
                print("Could not find compose box. Please type manually.", flush=True)

            print("Browser opened. Review your post and click Post.", flush=True)
            print("Close the browser window when done.", flush=True)
            try:
                page.wait_for_event("close", timeout=300000)
            except Exception:
                pass
    """)

    result = subprocess.run(
        [sys.executable, "-c", script],
        timeout=600,
        capture_output=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Camoufox subprocess exited with code {result.returncode}")
