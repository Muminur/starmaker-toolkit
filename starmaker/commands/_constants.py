"""Shared constants for the StarMaker command modules.

This module is the single source of truth for draft *filenames* and the set of
supported platform identifiers within the ``starmaker.commands`` package.

Note:
    ``starmaker.nlp.humanizer`` independently produces drafts using the same
    filenames. That module is owned by another unit and is not imported here to
    avoid a cross-package dependency; the constants below are the authoritative
    copy for everything inside ``starmaker.commands``. If the two ever drift,
    the humanizer output is what is parsed, so keep these in sync with it.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Platform identifiers
# ---------------------------------------------------------------------------

#: Canonical platform identifiers used across draft/post commands.
PLATFORM_REDDIT = "reddit"
PLATFORM_HACKERNEWS = "hackernews"
PLATFORM_DEVTO = "devto"
PLATFORM_TWITTER = "twitter"
PLATFORM_DISCORD = "discord"

#: Platforms for which credentials are optional (publishing falls back to a
#: browser flow instead of API keys).
BROWSER_PLATFORMS: frozenset[str] = frozenset({PLATFORM_HACKERNEWS, PLATFORM_TWITTER})


# ---------------------------------------------------------------------------
# Draft filenames
# ---------------------------------------------------------------------------

#: Single-file draft names keyed by platform. Reddit is intentionally excluded
#: because it produces one file *per subreddit* (see ``REDDIT_DRAFT_GLOB``).
DRAFT_FILENAMES: dict[str, str] = {
    PLATFORM_DEVTO: "devto_article.md",
    PLATFORM_TWITTER: "twitter_single.md",
    PLATFORM_DISCORD: "discord.md",
    PLATFORM_HACKERNEWS: "hackernews.md",
}

#: Glob matching every per-subreddit Reddit draft (e.g. ``reddit_r_python.md``).
REDDIT_DRAFT_GLOB = "reddit_r_*.md"

#: Filename prefix for Reddit drafts; full name is ``f"{REDDIT_DRAFT_PREFIX}{sub}.md"``.
REDDIT_DRAFT_PREFIX = "reddit_r_"


# ---------------------------------------------------------------------------
# Human-readable platform labels (used in Rich tables / summaries)
# ---------------------------------------------------------------------------

PLATFORM_LABELS: dict[str, str] = {
    PLATFORM_REDDIT: "Reddit",
    PLATFORM_DEVTO: "Dev.to",
    PLATFORM_TWITTER: "Twitter/X",
    PLATFORM_DISCORD: "Discord",
    PLATFORM_HACKERNEWS: "Hacker News",
}


def label_for_filename(filename: str) -> str:
    """Return a human-readable platform label for a draft *filename*.

    Args:
        filename: The draft filename (e.g. ``"devto_article.md"``).

    Returns:
        A display label such as ``"Dev.to"``, or ``"unknown"`` if the filename
        does not match any known platform.
    """
    for platform, label in PLATFORM_LABELS.items():
        if platform in filename:
            return label
    return "unknown"
