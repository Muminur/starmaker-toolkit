"""Markdown generation helpers."""

from __future__ import annotations


def make_table(headers: list[str], rows: list[list[str]]) -> str:
    """Generate a markdown table."""
    if not headers or not rows:
        return ""

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        # Pad row to match headers length
        padded = row + [""] * (len(headers) - len(row))
        lines.append("| " + " | ".join(padded[:len(headers)]) + " |")

    return "\n".join(lines)


def make_badge(label: str, value: str, color: str = "blue", url: str = "") -> str:
    """Generate a shields.io badge markdown."""
    badge_url = f"https://img.shields.io/badge/{_escape(label)}-{_escape(value)}-{color}"
    img = f"![{label}]({badge_url})"
    if url:
        return f"[{img}]({url})"
    return img


def make_github_badges(owner: str, repo: str) -> list[str]:
    """Generate standard GitHub repo badges."""
    base = f"https://github.com/{owner}/{repo}"
    return [
        f"[![GitHub stars](https://img.shields.io/github/stars/{owner}/{repo}?style=social)]({base})",
        f"[![GitHub forks](https://img.shields.io/github/forks/{owner}/{repo}?style=social)]({base}/fork)",
        f"[![GitHub license](https://img.shields.io/github/license/{owner}/{repo})]({base}/blob/main/LICENSE)",
        f"[![GitHub release](https://img.shields.io/github/v/release/{owner}/{repo})]({base}/releases)",
        f"[![GitHub issues](https://img.shields.io/github/issues/{owner}/{repo})]({base}/issues)",
    ]


def make_section(title: str, content: str, level: int = 2) -> str:
    """Generate a markdown section."""
    prefix = "#" * level
    return f"{prefix} {title}\n\n{content}"


def _escape(text: str) -> str:
    """Escape special characters for shields.io URLs."""
    return text.replace("-", "--").replace("_", "__").replace(" ", "_")
