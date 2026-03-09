"""Repository audit for star-worthiness."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table

from starmaker.utils.console import console
from starmaker.utils.github_api import RepoInfo, fetch_repo_info, get_local_repo_info


# Audit checks: (name, check_fn, suggestion, weight)
def _build_checks() -> list[tuple[str, callable, str, int]]:
    return [
        ("Has description", lambda r: r.has_description,
         "Add a clear, concise description to your repo", 10),
        ("Has topics/tags", lambda r: r.has_topics,
         "Add relevant topics (Settings > Topics) for discoverability", 10),
        ("Has 5+ topics", lambda r: len(r.topics) >= 5,
         "Add at least 5 topics — repos with more topics appear in more searches", 5),
        ("Has README", lambda r: r.has_readme,
         "Add a README.md — this is the first thing visitors see", 15),
        ("Has LICENSE", lambda r: r.has_license,
         "Add a LICENSE file — people won't star/use unlicensed code", 10),
        ("Has CONTRIBUTING", lambda r: r.has_contributing,
         "Add CONTRIBUTING.md — shows the project welcomes contributors", 5),
        ("Has CHANGELOG", lambda r: r.has_changelog,
         "Add CHANGELOG.md — shows active, organized development", 5),
        ("Has CI/CD", lambda r: r.has_ci,
         "Add GitHub Actions CI — builds trust and shows quality", 8),
        ("Has releases", lambda r: r.has_releases,
         "Create releases with binaries — makes it easy to use", 10),
        ("Has homepage/website", lambda r: r.has_homepage,
         "Add a homepage URL (repo settings) — projects with websites look more serious", 5),
        ("Has 1+ stars", lambda r: r.stars >= 1,
         "Get your first star — ask a friend or colleague", 3),
        ("Has 10+ stars", lambda r: r.stars >= 10,
         "Reach 10 stars — post on Reddit, HN, or Dev.to", 5),
        ("Has 2+ contributors", lambda r: r.contributor_count >= 2,
         "Get a contributor — even a typo fix counts", 5),
        ("Recent activity", lambda r: bool(r.updated_at),
         "Push recent commits — stale repos don't attract stars", 4),
    ]


def run(repo_url: str | None = None) -> None:
    """Audit a repository for star-worthiness."""
    if repo_url:
        console.print(f"\n[bold blue]Auditing {repo_url}...[/bold blue]\n")
        try:
            info = fetch_repo_info(repo_url)
        except (ValueError, ConnectionError) as e:
            console.print(f"[red]Error:[/red] {e}")
            return
    else:
        console.print("\n[bold blue]Auditing local repository...[/bold blue]\n")
        local = get_local_repo_info()
        if "remote_url" not in local:
            console.print("[red]Error:[/red] No git remote found. Use --url to specify a repo.")
            return
        try:
            info = fetch_repo_info(local["remote_url"])
        except (ValueError, ConnectionError) as e:
            console.print(f"[red]Error:[/red] {e}")
            return

    # Display repo overview
    overview = Table(title="Repository Overview", show_header=False, border_style="blue")
    overview.add_column("Field", style="bold")
    overview.add_column("Value")
    overview.add_row("Name", info.full_name or info.name)
    overview.add_row("Description", info.description or "[red]Missing![/red]")
    overview.add_row("Stars", str(info.stars))
    overview.add_row("Forks", str(info.forks))
    overview.add_row("Language", info.language)
    overview.add_row("License", info.license or "[red]None[/red]")
    overview.add_row("Topics", ", ".join(info.topics) if info.topics else "[red]None[/red]")
    overview.add_row("Releases", f"{info.release_count} (latest: {info.latest_release})" if info.has_releases else "[yellow]None[/yellow]")
    console.print(overview)

    # Run audit checks
    checks = _build_checks()
    score = 0
    max_score = sum(c[3] for c in checks)
    passed = 0
    failed_items = []

    results = Table(title="\nAudit Results", border_style="blue")
    results.add_column("Check", style="bold")
    results.add_column("Status", justify="center")
    results.add_column("Points", justify="right")

    for name, check_fn, suggestion, weight in checks:
        if check_fn(info):
            results.add_row(name, "[green]\u2713 Pass[/green]", f"+{weight}")
            score += weight
            passed += 1
        else:
            results.add_row(name, "[red]\u2717 Fail[/red]", f"+0/{weight}")
            failed_items.append((name, suggestion, weight))

    console.print(results)

    # Score summary
    pct = int((score / max_score) * 100) if max_score else 0
    if pct >= 80:
        grade, color = "A", "green"
    elif pct >= 60:
        grade, color = "B", "blue"
    elif pct >= 40:
        grade, color = "C", "yellow"
    else:
        grade, color = "D", "red"

    console.print(Panel(
        f"[bold {color}]Score: {score}/{max_score} ({pct}%) — Grade: {grade}[/bold {color}]\n"
        f"Passed: {passed}/{len(checks)} checks",
        title="Star-Worthiness Score",
        border_style=color,
    ))

    # Suggestions
    if failed_items:
        console.print("\n[bold yellow]Improvement Suggestions (by impact):[/bold yellow]\n")
        failed_items.sort(key=lambda x: x[2], reverse=True)
        for i, (name, suggestion, weight) in enumerate(failed_items, 1):
            console.print(f"  {i}. [bold]{name}[/bold] (+{weight} pts)")
            console.print(f"     {suggestion}\n")
