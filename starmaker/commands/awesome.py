"""Find awesome-lists and generate PR content."""

from __future__ import annotations

from pathlib import Path

import requests
from rich.panel import Panel
from rich.table import Table

from starmaker.config import StarMakerConfig
from starmaker.utils.console import console

# Common awesome-lists mapped by tag/language
AWESOME_LISTS = {
    "rust": [
        ("awesome-rust", "rust-unofficial/awesome-rust"),
        ("awesome-rust-tools", "aspect-build/rules_rust"),
    ],
    "python": [
        ("awesome-python", "vinta/awesome-python"),
        ("awesome-python-applications", "mahmoud/awesome-python-applications"),
    ],
    "typescript": [
        ("awesome-typescript", "dzharii/awesome-typescript"),
    ],
    "javascript": [
        ("awesome-javascript", "sorrycc/awesome-javascript"),
    ],
    "go": [
        ("awesome-go", "avelino/awesome-go"),
    ],
    "react": [
        ("awesome-react", "enaqx/awesome-react"),
    ],
    "tauri": [
        ("awesome-tauri", "nicholasgasior/awesome-tauri"),
    ],
    "cli": [
        ("awesome-cli-apps", "agarrharr/awesome-cli-apps"),
    ],
    "productivity": [
        ("awesome-productivity", "jyguyomarch/awesome-productivity"),
    ],
    "linux": [
        ("awesome-linux-software", "luong-komorebi/Awesome-Linux-Software"),
    ],
    "macos": [
        ("awesome-macos", "iCHAIT/awesome-macOS"),
        ("awesome-mac", "jaywcjlove/awesome-mac"),
    ],
    "privacy": [
        ("awesome-privacy", "pluja/awesome-privacy"),
    ],
    "open-source": [
        ("awesome-oss-alternatives", "RunaCapital/awesome-oss-alternatives"),
    ],
    "text-expansion": [
        ("awesome-productivity", "jyguyomarch/awesome-productivity"),
    ],
}


def _find_matching_lists(config: StarMakerConfig) -> list[tuple[str, str]]:
    """Find awesome-lists matching the project's tags."""
    matches = set()

    # From config
    for tag in config.project.tags:
        for name, repo in AWESOME_LISTS.get(tag.lower(), []):
            matches.add((name, repo))

    # From explicit config
    for list_name in config.promotion.awesome_lists:
        for tag_lists in AWESOME_LISTS.values():
            for name, repo in tag_lists:
                if list_name.lower() in name.lower():
                    matches.add((name, repo))

    return sorted(matches, key=lambda x: x[0])


def _generate_pr_body(config: StarMakerConfig, list_name: str) -> str:
    """Generate PR body for an awesome-list submission."""
    proj = config.project
    highlights = "\n".join(f"- {h}" for h in proj.highlights[:3]) if proj.highlights else ""

    return f"""## Add {proj.name}

**Project:** [{proj.name}]({proj.repo})
**Description:** {proj.tagline}

### Why it belongs in {list_name}

{proj.description}

**Key features:**
{highlights}

### Checklist

- [ ] Project is open source
- [ ] Project has a license
- [ ] Project is actively maintained
- [ ] Project has documentation
- [ ] Entry follows the list's formatting guidelines
- [ ] Entry is added in alphabetical order

### Suggested entry

```markdown
- [{proj.name}]({proj.repo}) - {proj.tagline}
```
"""


def run(config: StarMakerConfig, output_dir: str = "drafts") -> None:
    """Find awesome-lists and generate PR drafts."""
    if not config.project.name:
        console.print("[red]Error:[/red] No project configured. Run `starmaker init` first.")
        return

    console.print("\n[bold blue]Finding matching awesome-lists...[/bold blue]\n")
    matches = _find_matching_lists(config)

    if not matches:
        console.print("[yellow]No matching awesome-lists found for your tags.[/yellow]")
        console.print("Try adding more tags to your starmaker.yaml config.")
        return

    # Display matches
    table = Table(title="Matching Awesome Lists", border_style="blue")
    table.add_column("List", style="bold")
    table.add_column("Repository")
    table.add_column("URL")

    for name, repo in matches:
        table.add_row(name, repo, f"https://github.com/{repo}")

    console.print(table)

    # Generate PR drafts
    out = Path(output_dir) / "awesome-lists"
    out.mkdir(parents=True, exist_ok=True)

    for name, repo in matches:
        pr_body = _generate_pr_body(config, name)
        filepath = out / f"pr_{name}.md"
        filepath.write_text(pr_body, encoding="utf-8")
        console.print(f"  [green]\u2713[/green] {filepath}")

    console.print(Panel(
        f"[bold green]{len(matches)} PR draft(s) generated in ./{output_dir}/awesome-lists/[/bold green]\n\n"
        "Review each draft, then:\n"
        "1. Fork the awesome-list repo\n"
        "2. Add your entry (alphabetical order)\n"
        "3. Open a PR with the generated body",
        title="Done",
        border_style="green",
    ))
