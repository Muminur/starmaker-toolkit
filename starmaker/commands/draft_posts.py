"""Generate platform-specific promotional post drafts."""

from __future__ import annotations

from pathlib import Path

from rich.panel import Panel

from starmaker.config import StarMakerConfig
from starmaker.platforms import PLATFORMS
from starmaker.utils.console import console


def run(config: StarMakerConfig, platform: str | None = None, output_dir: str = "drafts") -> None:
    """Generate post drafts for configured platforms."""
    if not config.project.name:
        console.print("[red]Error:[/red] No project configured. Run `starmaker init` first.")
        return

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    platforms_to_run = [platform] if platform else config.promotion.platforms

    total_files = 0
    for plat in platforms_to_run:
        if plat not in PLATFORMS:
            console.print(f"[yellow]Warning:[/yellow] Unknown platform '{plat}', skipping.")
            continue

        console.print(f"\n[bold blue]Generating {plat} drafts...[/bold blue]")
        generator = PLATFORMS[plat]
        drafts = generator(config)

        for filename, content in drafts.items():
            filepath = out / filename
            filepath.write_text(content, encoding="utf-8")
            console.print(f"  [green]\u2713[/green] {filepath}")
            total_files += 1

    console.print(Panel(
        f"[bold green]{total_files} draft(s) generated in ./{output_dir}/[/bold green]\n\n"
        "Review and customize each draft before posting manually.",
        title="Done",
        border_style="green",
    ))
