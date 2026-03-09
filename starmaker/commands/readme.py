"""README enhancement suggestions."""

from __future__ import annotations

from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from starmaker.config import StarMakerConfig
from starmaker.utils.console import console
from starmaker.utils.github_api import parse_github_url
from starmaker.utils.markdown import make_github_badges

# Sections that high-star READMEs typically have
RECOMMENDED_SECTIONS = [
    ("Badges", "shields.io badges for stars, license, version, CI status"),
    ("Logo/Banner", "A project logo or banner image at the top"),
    ("Description", "1-2 sentence tagline + longer description"),
    ("Screenshot/GIF", "Visual demo of the project in action"),
    ("Features", "Bulleted list of key features"),
    ("Why This Project", "Comparison with alternatives or unique value proposition"),
    ("Quick Start", "Minimal steps to get running (install + first use)"),
    ("Installation", "Detailed installation instructions for each platform"),
    ("Usage", "Common usage examples with code blocks"),
    ("Configuration", "How to configure the project"),
    ("Contributing", "How to contribute (or link to CONTRIBUTING.md)"),
    ("License", "License type with link"),
    ("Acknowledgments", "Credits and thanks"),
]


def _check_readme_sections(readme_content: str) -> list[tuple[str, str, bool]]:
    """Check which recommended sections exist in the README."""
    lower = readme_content.lower()
    results = []
    for section, description in RECOMMENDED_SECTIONS:
        # Check for section header
        found = any(
            marker in lower
            for marker in [
                f"# {section.lower()}",
                f"## {section.lower()}",
                f"### {section.lower()}",
                section.lower().replace(" ", "-"),
            ]
        )
        # Special checks
        if section == "Badges":
            found = "shields.io" in lower or "![" in readme_content[:500]
        elif section == "Logo/Banner":
            found = any(ext in lower[:1000] for ext in [".png", ".svg", ".jpg", "logo"])
        elif section == "Screenshot/GIF":
            found = any(ext in lower for ext in [".gif", "screenshot", "demo"])

        results.append((section, description, found))
    return results


def run(config: StarMakerConfig, readme_path: str | None = None, output_dir: str = "drafts") -> None:
    """Analyze README and suggest enhancements."""
    proj = config.project

    # Find README
    if readme_path:
        rpath = Path(readme_path)
    else:
        rpath = Path("README.md")
        if not rpath.exists():
            rpath = Path("readme.md")

    readme_content = ""
    if rpath.exists():
        readme_content = rpath.read_text(encoding="utf-8")
        console.print(f"\n[bold blue]Analyzing {rpath}...[/bold blue]\n")
    else:
        console.print("\n[bold yellow]No README found — generating recommendations from scratch.[/bold yellow]\n")

    # Section check
    sections = _check_readme_sections(readme_content)

    table = Table(title="README Section Audit", border_style="blue")
    table.add_column("Section", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Description")

    present = 0
    for section, description, found in sections:
        status = "[green]\u2713 Found[/green]" if found else "[red]\u2717 Missing[/red]"
        table.add_row(section, status, description)
        if found:
            present += 1

    console.print(table)

    pct = int((present / len(sections)) * 100)
    console.print(f"\n[bold]README completeness: {present}/{len(sections)} ({pct}%)[/bold]\n")

    # Generate badges
    badges_md = ""
    if proj.repo:
        parsed = parse_github_url(proj.repo)
        if parsed:
            owner, repo = parsed
            badges = make_github_badges(owner, repo)
            badges_md = " ".join(badges)

    # Generate suggested additions
    suggestions = []

    if badges_md:
        suggestions.append(("Badges (paste at top of README)", badges_md))

    missing = [(s, d) for s, d, found in sections if not found]
    if missing:
        for section, description in missing:
            if section == "Screenshot/GIF":
                suggestions.append((
                    "Screenshot/Demo GIF",
                    f"<!-- Add a screenshot or GIF demo here -->\n"
                    f"![{proj.name} Demo](./docs/demo.gif)\n\n"
                    f"*Tip: Use [gifcap](https://gifcap.dev) or [peek](https://github.com/phw/peek) to record.*",
                ))
            elif section == "Quick Start":
                suggestions.append((
                    "Quick Start Section",
                    f"## Quick Start\n\n"
                    f"```bash\n"
                    f"# Install {proj.name}\n"
                    f"# [Add install command here]\n\n"
                    f"# Run\n"
                    f"# [Add run command here]\n"
                    f"```",
                ))
            elif section == "Why This Project":
                competitors_text = ", ".join(proj.competitors[:3]) if proj.competitors else "alternatives"
                suggestions.append((
                    "Why This Project Section",
                    f"## Why {proj.name}?\n\n"
                    f"Unlike {competitors_text}, {proj.name}:\n\n"
                    + "\n".join(f"- **{h}**" for h in proj.highlights[:5]),
                ))

    # Write suggestions
    if suggestions:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        output = f"# README Enhancement Suggestions for {proj.name}\n\n"
        for title, content in suggestions:
            output += f"## {title}\n\n```markdown\n{content}\n```\n\n---\n\n"

        filepath = out / "readme_suggestions.md"
        filepath.write_text(output, encoding="utf-8")

        console.print(Panel(
            f"[bold green]Suggestions saved to {filepath}[/bold green]\n\n"
            "Copy relevant sections into your README.",
            title="Done",
            border_style="green",
        ))
    else:
        console.print(Panel(
            "[bold green]Your README looks great! No major suggestions.[/bold green]",
            title="Done",
            border_style="green",
        ))
