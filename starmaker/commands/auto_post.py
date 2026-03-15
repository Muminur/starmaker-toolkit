"""Auto-generate and publish posts from a README.md file.

Reads a README, extracts key info using pure Python NLP,
generates platform-specific drafts, and publishes them.
"""
from __future__ import annotations

from pathlib import Path

from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from starmaker.nlp.readme_parser import parse_readme, build_config_from_readme
from starmaker.nlp.humanizer import generate_all_drafts
from starmaker.utils.console import console


def run(
    readme_path: str,
    *,
    repo_url: str = "",
    platform: str | None = None,
    output_dir: str = "drafts",
    dry_run: bool = False,
    skip_confirm: bool = False,
    publish: bool = False,
) -> None:
    """Generate and optionally publish posts from a README.

    Args:
        readme_path: Path to README.md file
        repo_url: GitHub repo URL (auto-detected if not provided)
        platform: Generate for specific platform only
        output_dir: Directory to save draft files
        dry_run: Preview posts without publishing
        publish: Publish after generating drafts
        skip_confirm: Skip confirmation prompt
    """
    # Read README
    readme_file = Path(readme_path)
    if not readme_file.exists():
        console.print(f"[red]README not found: {readme_path}[/red]")
        return

    readme_text = readme_file.read_text(encoding="utf-8")
    console.print(f"[dim]Reading {readme_file.name} ({len(readme_text)} chars)...[/dim]")

    # Parse README with NLP
    content = parse_readme(readme_text)
    if repo_url:
        content.repo_url = repo_url
    elif not content.repo_url:
        # Try to detect from git
        from starmaker.config import detect_local_repo
        local = detect_local_repo()
        content.repo_url = local.get("repo", "")

    # Show what was extracted
    console.print(Panel(
        f"[bold]Title:[/bold] {content.title}\n"
        f"[bold]Tagline:[/bold] {content.tagline}\n"
        f"[bold]Description:[/bold] {content.description[:200]}...\n"
        f"[bold]Highlights:[/bold] {len(content.highlights)} found\n"
        f"[bold]Tags:[/bold] {', '.join(content.tags[:8])}\n"
        f"[bold]Repo:[/bold] {content.repo_url}",
        title="README Analysis",
        border_style="cyan",
    ))

    if not content.title:
        console.print("[red]Could not extract project title from README.[/red]")
        return

    # Determine subreddits from tags
    tag_sub_map = {
        "rust": "rust", "python": "Python", "javascript": "javascript",
        "typescript": "typescript", "react": "reactjs", "linux": "linux",
        "macos": "macapps", "cli": "commandline", "privacy": "privacy",
        "open-source": "opensource", "desktop": "software",
    }
    subreddits = ["opensource", "programming"]
    for tag in content.tags:
        sub = tag_sub_map.get(tag.lower())
        if sub and sub not in subreddits:
            subreddits.append(sub)

    # Generate drafts
    if platform:
        # Single platform
        from starmaker.nlp.humanizer import (
            humanize_for_reddit, humanize_for_devto, humanize_for_twitter,
            humanize_for_discord, humanize_for_hackernews,
        )
        generators = {
            "reddit": lambda: humanize_for_reddit(content, subreddits),
            "devto": lambda: humanize_for_devto(content),
            "twitter": lambda: humanize_for_twitter(content),
            "discord": lambda: humanize_for_discord(content),
            "hackernews": lambda: humanize_for_hackernews(content),
        }
        if platform not in generators:
            console.print(f"[red]Unknown platform: {platform}[/red]")
            console.print(f"Available: {', '.join(generators.keys())}")
            return
        drafts = generators[platform]()
    else:
        drafts = generate_all_drafts(content, subreddits)

    # Write draft files
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    table = Table(title="Generated Drafts", border_style="green")
    table.add_column("File", style="bold")
    table.add_column("Platform")
    table.add_column("Size")

    for filename, file_content in drafts.items():
        filepath = out_path / filename
        filepath.write_text(file_content, encoding="utf-8")

        # Determine platform from filename
        plat = "unknown"
        if "reddit" in filename:
            plat = "Reddit"
        elif "devto" in filename:
            plat = "Dev.to"
        elif "twitter" in filename:
            plat = "Twitter/X"
        elif "discord" in filename:
            plat = "Discord"
        elif "hackernews" in filename:
            plat = "Hacker News"

        table.add_row(filename, plat, f"{len(file_content)} chars")

    console.print(table)
    console.print(f"\n[green]Drafts saved to {out_path}/[/green]")

    # Dry run: show previews
    if dry_run:
        for filename, file_content in drafts.items():
            console.print(Panel(
                file_content[:500] + ("..." if len(file_content) > 500 else ""),
                title=filename,
                border_style="dim",
            ))
        return

    # Publish if requested
    if publish:
        if not skip_confirm:
            if not Confirm.ask("\n[bold]Publish these drafts now?[/bold]", default=False):
                console.print("[dim]Skipped publishing. Run [cyan]starmaker post[/cyan] to publish later.[/dim]")
                return

        console.print("\n[bold blue]Publishing...[/bold blue]\n")
        # Use the existing post command
        from starmaker.commands.post import run as run_post
        config = build_config_from_readme(readme_text, content.repo_url)
        run_post(config, platform=platform, drafts_dir=output_dir, dry_run=False, skip_confirm=True)
    else:
        console.print("\n[dim]To publish: run [cyan]starmaker post[/cyan] or add --publish flag.[/dim]")
