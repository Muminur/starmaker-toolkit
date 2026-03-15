"""Post generated drafts to platforms via official APIs."""

from __future__ import annotations

import re
from pathlib import Path

from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from starmaker.config import StarMakerConfig
from starmaker.credentials import load_credentials, init_credentials, CREDENTIALS_DIR
from starmaker.publishers import PUBLISHERS
from starmaker.publishers.base import PostResult
from starmaker.utils.console import console


def _parse_reddit_draft(filepath: Path) -> tuple[str, str, str]:
    """Extract title, body, and subreddit from a Reddit draft file."""
    content = filepath.read_text(encoding="utf-8")

    # Extract subreddit from filename
    match = re.search(r"reddit_r_(.+)\.md$", filepath.name)
    subreddit = match.group(1) if match else "test"

    # Extract title
    title_match = re.search(r"\*\*Title:\*\*\s*(.+)", content)
    title = title_match.group(1).strip() if title_match else ""

    # Extract body (everything after **Body:**)
    body_match = re.search(r"\*\*Body:\*\*\s*\n\n(.+)", content, re.DOTALL)
    body = body_match.group(1).strip() if body_match else content

    return title, body, subreddit


def _parse_hn_draft(filepath: Path) -> tuple[str, str, str]:
    """Extract title, text, and URL from HN draft."""
    content = filepath.read_text(encoding="utf-8")

    title_match = re.search(r"\*\*Title:\*\*\s*(.+)", content)
    title = title_match.group(1).strip() if title_match else ""

    url_match = re.search(r"\*\*URL:\*\*\s*(.+)", content)
    url = url_match.group(1).strip() if url_match else ""

    text_match = re.search(r"\*\*Text \(optional.*?\):\*\*\s*\n\n(.+?)(\n---|\Z)", content, re.DOTALL)
    text = text_match.group(1).strip() if text_match else ""

    return title, text, url


def _parse_devto_draft(filepath: Path) -> tuple[str, str, list[str]]:
    """Extract title, body, and tags from Dev.to draft."""
    content = filepath.read_text(encoding="utf-8")

    # Parse frontmatter
    title = ""
    tags: list[str] = []

    fm_match = re.search(r"---\n(.+?)\n---", content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        title_match = re.search(r'title:\s*"(.+?)"', fm)
        if title_match:
            title = title_match.group(1)
        tags_match = re.search(r"tags:\s*(.+)", fm)
        if tags_match:
            tags = [t.strip() for t in tags_match.group(1).split(",")]

    # Body is everything after frontmatter, before the tips section
    body_match = re.search(r"---\n\n(.+?)(\n---\n\n## Dev\.to Publishing Tips|\Z)", content, re.DOTALL)
    body = body_match.group(1).strip() if body_match else content

    return title, body, tags


def _parse_twitter_single(filepath: Path) -> str:
    """Extract tweet text from single tweet draft."""
    content = filepath.read_text(encoding="utf-8")
    # Remove the header and tips
    lines = content.split("\n")
    tweet_lines = []
    skip = True
    for line in lines:
        if line.startswith("# "):
            skip = False
            continue
        if line.startswith("---"):
            break
        if not skip:
            tweet_lines.append(line)
    return "\n".join(tweet_lines).strip()


def _parse_discord_draft(filepath: Path) -> str:
    """Extract Discord message from draft."""
    content = filepath.read_text(encoding="utf-8")

    # Extract content between "Post this in..." and "---"
    match = re.search(
        r"\*\*Post this in #showcase.*?\*\*\s*\n\n(.+?)\n---",
        content,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    # Fallback: everything between first blank line and first ---
    parts = content.split("---")
    if len(parts) > 1:
        return parts[0].strip()
    return content


def run(
    config: StarMakerConfig,
    platform: str | None = None,
    drafts_dir: str = "drafts",
    dry_run: bool = False,
    skip_confirm: bool = False,
) -> None:
    """Post drafts to platforms."""
    drafts = Path(drafts_dir)
    if not drafts.exists():
        console.print("[red]Error:[/red] No drafts directory found. Run `starmaker draft` first.")
        return

    # Load credentials
    credentials = load_credentials()
    if not credentials:
        init_credentials()
        console.print(Panel(
            f"[yellow]No credentials found.[/yellow]\n\n"
            "Set credentials using any of these methods:\n"
            "  [cyan]1.[/cyan] Set environment variables (e.g. REDDIT_CLIENT_ID)\n"
            "  [cyan]2.[/cyan] Create a .env file (copy from .env.example)\n"
            f"  [cyan]3.[/cyan] Edit {CREDENTIALS_DIR / 'credentials.yaml'}\n"
            "  [cyan]4.[/cyan] Run [cyan]starmaker setup[/cyan] for browser-based setup\n\n"
            "Then run [cyan]starmaker post[/cyan] again.\n\n"
            "[bold]Required keys by platform:[/bold]\n"
            "  Reddit:  reddit_client_id, reddit_client_secret, reddit_username, reddit_password\n"
            "  Dev.to:  devto_api_key\n"
            "  Twitter: (optional) twitter_api_key, etc. — falls back to browser\n"
            "  Discord: discord_webhook_urls\n"
            "  HN:      (none) — opens browser",
            title="Setup Required",
            border_style="yellow",
        ))
        return

    # Determine which platforms to post to
    if platform:
        platforms_to_post = [platform]
    else:
        platforms_to_post = config.promotion.platforms

    # Collect all posts to make
    posts: list[dict] = []

    for plat in platforms_to_post:
        if plat == "reddit":
            for draft_file in sorted(drafts.glob("reddit_r_*.md")):
                title, body, subreddit = _parse_reddit_draft(draft_file)
                posts.append({
                    "platform": "reddit",
                    "file": draft_file.name,
                    "title": title,
                    "body": body,
                    "kwargs": {"subreddit": subreddit},
                    "display": f"Reddit r/{subreddit}",
                })

        elif plat == "hackernews":
            hn_file = drafts / "hackernews.md"
            if hn_file.exists():
                title, text, url = _parse_hn_draft(hn_file)
                posts.append({
                    "platform": "hackernews",
                    "file": hn_file.name,
                    "title": title,
                    "body": text,
                    "kwargs": {"url": url},
                    "display": "Hacker News (Show HN)",
                })

        elif plat == "devto":
            devto_file = drafts / "devto_article.md"
            if devto_file.exists():
                title, body, tags = _parse_devto_draft(devto_file)
                posts.append({
                    "platform": "devto",
                    "file": devto_file.name,
                    "title": title,
                    "body": body,
                    "kwargs": {"tags": tags, "published": False},
                    "display": "Dev.to (draft)",
                })

        elif plat == "twitter":
            tw_file = drafts / "twitter_single.md"
            if tw_file.exists():
                tweet = _parse_twitter_single(tw_file)
                posts.append({
                    "platform": "twitter",
                    "file": tw_file.name,
                    "title": "",
                    "body": tweet,
                    "kwargs": {},
                    "display": "Twitter/X",
                })

        elif plat == "discord":
            dc_file = drafts / "discord.md"
            if dc_file.exists():
                message = _parse_discord_draft(dc_file)
                posts.append({
                    "platform": "discord",
                    "file": dc_file.name,
                    "title": "",
                    "body": message,
                    "kwargs": {},
                    "display": "Discord",
                })

    if not posts:
        console.print("[yellow]No drafts found to post.[/yellow] Run `starmaker draft` first.")
        return

    # Show preview
    preview = Table(title="Posts to Publish", border_style="blue")
    preview.add_column("#", justify="right", style="dim")
    preview.add_column("Platform", style="bold")
    preview.add_column("Title / Preview")
    preview.add_column("Status")

    for i, post in enumerate(posts, 1):
        pub_cls = PUBLISHERS.get(post["platform"])
        if pub_cls:
            pub = pub_cls()
            has_creds = pub.validate_credentials(credentials)
            status = "[green]Ready[/green]" if has_creds else "[yellow]Browser[/yellow]" if post["platform"] in ("hackernews", "twitter") else "[red]Missing keys[/red]"
        else:
            status = "[red]Unknown[/red]"

        title_preview = (post["title"] or post["body"])[:60]
        preview.add_row(str(i), post["display"], title_preview, status)

    console.print(preview)

    if dry_run:
        console.print("\n[dim]Dry run — no posts will be published.[/dim]")
        return

    if not skip_confirm:
        if not Confirm.ask(f"\n[bold]Publish {len(posts)} post(s)?[/bold]"):
            console.print("[dim]Cancelled.[/dim]")
            return

    # Publish
    results: list[PostResult] = []
    console.print()

    for post in posts:
        pub_cls = PUBLISHERS.get(post["platform"])
        if not pub_cls:
            results.append(PostResult(
                platform=post["display"],
                success=False,
                error="Unknown platform",
            ))
            continue

        pub = pub_cls()

        if not pub.validate_credentials(credentials) and post["platform"] not in ("hackernews", "twitter"):
            missing = pub.get_missing_keys(credentials)
            results.append(PostResult(
                platform=post["display"],
                success=False,
                error=f"Missing credentials: {', '.join(missing)}",
            ))
            console.print(f"  [red]x[/red] {post['display']}: Missing API keys")
            continue

        console.print(f"  [blue]>[/blue] Publishing to {post['display']}...")
        result = pub.publish(
            title=post["title"],
            body=post["body"],
            credentials=credentials,
            **post["kwargs"],
        )
        results.append(result)

        if result.success:
            url_text = f" -> {result.url}" if result.url else ""
            console.print(f"  [green]v[/green] {post['display']}: {result.message}{url_text}")
        else:
            console.print(f"  [red]x[/red] {post['display']}: {result.error}")

    # Summary
    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count

    console.print(Panel(
        f"[bold]Published: {success_count}/{len(results)}[/bold]\n"
        + (f"[red]Failed: {fail_count}[/red]" if fail_count else "[green]All successful![/green]"),
        title="Results",
        border_style="green" if fail_count == 0 else "yellow",
    ))
