"""Markdown generation helpers.

Utilities for building GitHub-flavored markdown tables, shields.io badges,
and sections.
"""

from __future__ import annotations


def make_table(headers: list[str], rows: list[list[str]]) -> str:
    """Generate a GitHub-flavored markdown table.

    Width-mismatch rule: rows with *fewer* cells than ``headers`` are padded
    with empty strings so every column is filled. Rows with *more* cells than
    there are headers are an error (data would be silently dropped), so a
    :class:`ValueError` is raised.

    Args:
        headers: Column header labels.
        rows: List of rows; each row is a list of cell strings.

    Returns:
        The rendered markdown table, or an empty string if ``headers`` or
        ``rows`` is empty.

    Raises:
        ValueError: If any row has more cells than there are headers.
    """
    if not headers or not rows:
        return ""

    width = len(headers)
    for i, row in enumerate(rows):
        if len(row) > width:
            raise ValueError(
                f"Row {i} has {len(row)} cells but table has only {width} "
                f"column(s): {row!r}"
            )

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        # Pad short rows to the header width.
        padded = list(row) + [""] * (width - len(row))
        lines.append("| " + " | ".join(padded) + " |")

    return "\n".join(lines)


def make_badge(label: str, value: str, color: str = "blue", url: str = "") -> str:
    """Generate a shields.io badge in markdown.

    Args:
        label: Left-hand label text.
        value: Right-hand value text.
        color: Badge color (a shields.io color name or hex).
        url: Optional link target; if given, the badge becomes a link.

    Returns:
        Markdown for the badge (optionally wrapped in a link).
    """
    badge_url = f"https://img.shields.io/badge/{_escape(label)}-{_escape(value)}-{color}"
    img = f"![{label}]({badge_url})"
    if url:
        return f"[{img}]({url})"
    return img


def make_github_badges(owner: str, repo: str) -> list[str]:
    """Generate a standard set of GitHub repo badges.

    Args:
        owner: Repository owner.
        repo: Repository name.

    Returns:
        A list of markdown badge strings (stars, forks, license, release,
        issues).
    """
    base = f"https://github.com/{owner}/{repo}"
    return [
        f"[![GitHub stars](https://img.shields.io/github/stars/{owner}/{repo}?style=social)]({base})",
        f"[![GitHub forks](https://img.shields.io/github/forks/{owner}/{repo}?style=social)]({base}/fork)",
        f"[![GitHub license](https://img.shields.io/github/license/{owner}/{repo})]({base}/blob/main/LICENSE)",
        f"[![GitHub release](https://img.shields.io/github/v/release/{owner}/{repo})]({base}/releases)",
        f"[![GitHub issues](https://img.shields.io/github/issues/{owner}/{repo})]({base}/issues)",
    ]


def make_section(title: str, content: str, level: int = 2) -> str:
    """Generate a markdown section with a heading.

    Args:
        title: Section heading text.
        content: Section body.
        level: Heading level (number of leading ``#``).

    Returns:
        The rendered section.
    """
    prefix = "#" * level
    return f"{prefix} {title}\n\n{content}"


def _escape(text: str) -> str:
    """Escape text for use in a shields.io static badge path segment.

    Follows shields.io's escaping rules for the ``/badge/<label>-<value>-<color>``
    path so that literal dashes, underscores, and spaces survive intact:

    * a literal ``-`` becomes ``--``;
    * a literal ``_`` becomes ``__``;
    * a literal space becomes ``_``.

    The replacements are ordered so each only touches the original character,
    never a substitution emitted by an earlier step (dashes and underscores are
    expanded before spaces collapse to a single underscore). A non-string input
    is coerced via :func:`str`.

    Args:
        text: The raw label or value text.

    Returns:
        The escaped string, safe to embed in a shields.io badge URL.
    """
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("-", "--")
        .replace("_", "__")
        .replace(" ", "_")
    )
