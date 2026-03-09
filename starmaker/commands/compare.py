"""Generate feature comparison tables."""

from __future__ import annotations

from pathlib import Path

from rich.panel import Panel

from starmaker.config import StarMakerConfig
from starmaker.utils.console import console
from starmaker.utils.markdown import make_table

# Default features to compare for common project types
DEFAULT_FEATURES = [
    "Open Source",
    "Free",
    "Privacy-Focused (Local Only)",
    "Cross-Platform",
    "Active Development",
    "Plugin/Extension Support",
    "CLI Support",
    "GUI",
]


def run(config: StarMakerConfig, output_dir: str = "drafts") -> None:
    """Generate a feature comparison table."""
    proj = config.project

    if not proj.name:
        console.print("[red]Error:[/red] No project configured. Run `starmaker init` first.")
        return

    comparison = config.promotion.comparison
    features = comparison.get("features", DEFAULT_FEATURES)
    competitors_data = comparison.get("competitors", {})

    if not proj.competitors and not competitors_data:
        console.print("[yellow]Warning:[/yellow] No competitors configured.")
        console.print("Add competitors to your starmaker.yaml under project.competitors")
        return

    # Build comparison table
    headers = ["Feature", proj.name] + (
        list(competitors_data.keys()) if competitors_data
        else proj.competitors
    )

    rows = []
    for i, feature in enumerate(features):
        row = [feature, "\u2705"]  # Your project gets a checkmark by default

        if competitors_data:
            for comp_name, comp_features in competitors_data.items():
                if i < len(comp_features):
                    row.append("\u2705" if comp_features[i] else "\u274c")
                else:
                    row.append("?")
        else:
            # Without detailed data, use "?" for competitors
            for _ in proj.competitors:
                row.append("?")

        rows.append(row)

    table_md = make_table(headers, rows)

    # Build full comparison section
    output = f"""# Feature Comparison

## {proj.name} vs Alternatives

{table_md}

*\u2705 = Supported | \u274c = Not supported | ? = Unknown — please verify*

---

### How to use this:

1. **Verify competitor features** — replace "?" with \u2705 or \u274c after checking
2. **Add to your README** — paste the table in a "## Comparison" or "## Why {proj.name}?" section
3. **Be honest** — don't misrepresent competitors. Credibility matters.
4. **Highlight your strengths** — reorder features to put your unique advantages first

### Suggested README section:

```markdown
## Why {proj.name}?

{table_md}

*{proj.name} is the only [key differentiator] that [unique value proposition].*
```
"""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    filepath = out / "comparison.md"
    filepath.write_text(output, encoding="utf-8")

    console.print(Panel(
        f"[bold green]Comparison table generated: {filepath}[/bold green]\n\n"
        "Review and verify competitor features before using.",
        title="Done",
        border_style="green",
    ))
