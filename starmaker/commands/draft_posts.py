"""Generate platform-specific promotional post drafts."""

from __future__ import annotations

from pathlib import Path

from rich.panel import Panel

from starmaker.config import StarMakerConfig
from starmaker.platforms import PLATFORMS
from starmaker.utils.console import console


def run(
    config: StarMakerConfig,
    platform: str | None = None,
    output_dir: str = "drafts",
) -> None:
    """Generate post drafts for configured platforms.

    Args:
        config: Loaded StarMaker configuration.
        platform: If given, generate drafts only for this platform. When an
            explicit but unknown platform is supplied, the command fails loudly
            (prints a clear error and returns) instead of silently producing
            nothing.
        output_dir: Directory where draft files are written.
    """
    if not config.project.name:
        console.print("[red]Error:[/red] No project configured. Run `starmaker init` first.")
        return

    # Fail loudly when the user explicitly asks for an unknown platform.
    if platform is not None and platform not in PLATFORMS:
        console.print(f"[red]Error:[/red] Unknown platform '{platform}'.")
        console.print(f"Available: {', '.join(sorted(PLATFORMS))}")
        return

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    platforms_to_run = [platform] if platform else config.promotion.platforms

    total_files = 0
    for plat in platforms_to_run:
        # platforms_to_run may contain config-derived names we don't recognise;
        # those are skipped with a warning (only an *explicit* --platform fails
        # loudly, handled above).
        generator = PLATFORMS.get(plat)
        if generator is None:
            console.print(f"[yellow]Warning:[/yellow] Unknown platform '{plat}', skipping.")
            continue

        console.print(f"\n[bold blue]Generating {plat} drafts...[/bold blue]")
        drafts = generator(config)

        for filename, content in drafts.items():
            filepath = out / filename
            try:
                filepath.write_text(content, encoding="utf-8")
            except OSError as exc:
                console.print(f"  [red]✗[/red] Failed to write {filepath}: {exc}")
                continue
            console.print(f"  [green]✓[/green] {filepath}")
            total_files += 1

    console.print(Panel(
        f"[bold green]{total_files} draft(s) generated in ./{output_dir}/[/bold green]\n\n"
        "Review and customize each draft before posting manually.",
        title="Done",
        border_style="green",
    ))
