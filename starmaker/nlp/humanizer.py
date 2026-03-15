"""Platform-specific post humanizer.

Generates natural, human-like drafts from parsed README content using
randomized templates. No LLM required -- pure template + variation logic.

Output formats match the exact draft file formats expected by
``starmaker.commands.post`` parsers (``_parse_reddit_draft``, etc.).
"""

from __future__ import annotations

import random
from typing import Sequence

from starmaker.nlp.readme_parser import ReadmeContent

# ---------------------------------------------------------------------------
# Template pools
# ---------------------------------------------------------------------------

REDDIT_OPENERS: list[str] = [
    "Hey r/{sub}! I've been working on {name} and wanted to share it with you all.",
    "Hi everyone! Just released {name} -- {tagline}.",
    "Hey r/{sub}, I built {name} because I was frustrated with existing options.",
    "Sharing my project {name} with the community -- {tagline}.",
    "I've been building {name} for a while now and it's finally ready to share!",
]

REDDIT_CLOSERS: list[str] = [
    "What do you think? I'd love to hear your feedback!",
    "Would love to get your thoughts on this!",
    "Happy to answer any questions -- let me know what you think!",
    "Feedback and suggestions welcome!",
    "I'd appreciate any feedback. Thanks for checking it out!",
]

DEVTO_INTROS: list[str] = [
    "I built {name} to solve a common problem: {description}",
    "{name} is {tagline}.",
    "After trying several tools, I decided to build my own: {name}.",
    "I wanted a tool that was {tagline}, so I built {name}.",
]

TWEET_TEMPLATES: list[str] = [
    "{name} -- {tagline}\n\n{repo_url}\n\n{hashtags}",
    "Just released {name}! {tagline}\n\n{repo_url}\n\n{hashtags}",
    "Introducing {name}: {tagline}\n\n{repo_url} {hashtags}",
    "Built {name} -- {tagline}\n\n{repo_url} {hashtags}",
]

HN_TITLES: list[str] = [
    "Show HN: {name} \u2013 {tagline}",
    "Show HN: {name} \u2013 {short_desc}",
]

DEFAULT_SUBREDDITS: list[str] = ["opensource", "commandline", "programming"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pick(templates: Sequence[str], **kwargs: str) -> str:
    """Pick a random template and format it."""
    return random.choice(templates).format(**kwargs)


def _bullet_highlights(highlights: list[str], max_items: int = 6) -> str:
    """Format highlights as markdown bullet list."""
    items = highlights[:max_items]
    return "\n".join(f"- {h}" for h in items)


def _hashtags(tags: list[str], limit: int = 5) -> str:
    """Build hashtag string from tags."""
    clean = [t.replace("-", "") for t in tags[:limit]]
    return " ".join(f"#{t}" for t in clean)


def _truncate(text: str, max_len: int, suffix: str = "...") -> str:
    """Truncate *text* to *max_len* chars, appending *suffix* if cut."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


# ---------------------------------------------------------------------------
# Platform humanizers
# ---------------------------------------------------------------------------


def humanize_for_reddit(
    content: ReadmeContent,
    subreddits: list[str] | None = None,
) -> dict[str, str]:
    """Generate Reddit post drafts.

    Returns ``{"reddit_r_{sub}.md": formatted_content}`` for each subreddit.
    Format matches ``_parse_reddit_draft()`` in ``post.py``.
    """
    subs = subreddits or list(DEFAULT_SUBREDDITS)

    highlights_md = _bullet_highlights(content.highlights)
    tech_md = ", ".join(content.tech_stack) if content.tech_stack else ""

    drafts: dict[str, str] = {}
    for sub in subs:
        opener = _pick(
            REDDIT_OPENERS,
            sub=sub,
            name=content.title,
            tagline=content.tagline,
        )
        closer = random.choice(REDDIT_CLOSERS)

        title = f"I built {content.title} \u2014 {content.tagline}"
        title = _truncate(title, 300)

        body_parts = [
            opener,
            "",
            content.description,
            "",
        ]

        if highlights_md:
            body_parts.extend(["**Key highlights:**", highlights_md, ""])

        if tech_md:
            body_parts.extend([f"**Built with:** {tech_md}", ""])

        body_parts.extend([
            f"GitHub: {content.repo_url}",
            "",
            closer,
        ])

        body = "\n".join(body_parts)

        draft = (
            f"# Reddit Post for r/{sub}\n\n"
            f"**Title:** {title}\n\n"
            f"**Body:**\n\n"
            f"{body}"
        )
        drafts[f"reddit_r_{sub}.md"] = draft

    return drafts


def humanize_for_devto(content: ReadmeContent) -> dict[str, str]:
    """Generate a Dev.to article draft.

    Returns ``{"devto_article.md": formatted_content}``.
    Format matches ``_parse_devto_draft()`` in ``post.py``.
    """
    tags = content.tags[:4]
    tags_str = ", ".join(tags) if tags else "opensource"

    intro = _pick(
        DEVTO_INTROS,
        name=content.title,
        tagline=content.tagline,
        description=content.description,
    )

    highlights_md = _bullet_highlights(content.highlights)
    tech_md = ", ".join(content.tech_stack) if content.tech_stack else ""

    article = f"""---
title: "Introducing {content.title}: {content.tagline}"
published: false
tags: {tags_str}
cover_image: ""
---

## What is {content.title}?

{intro}

{content.description}

## Key Features

{highlights_md}

{("## Tech Stack" + chr(10) + chr(10) + tech_md + chr(10)) if tech_md else ""}
## Getting Started

Check out the repository for installation instructions and documentation:

- GitHub: [{content.title}]({content.repo_url})

If you find it useful, a star on GitHub would be appreciated!

---

*{content.title} is free and open-source. Contributions welcome!*
"""

    return {"devto_article.md": article}


def humanize_for_twitter(content: ReadmeContent) -> dict[str, str]:
    """Generate a Twitter/X single post draft.

    Returns ``{"twitter_single.md": formatted_content}``.
    Format matches ``_parse_twitter_single()`` in ``post.py``.
    The tweet text MUST be under 280 characters.
    """
    hashtags = _hashtags(content.tags, limit=3)

    # Try each template until one fits in 280 chars
    tweet = ""
    templates = list(TWEET_TEMPLATES)
    random.shuffle(templates)

    for tmpl in templates:
        candidate = tmpl.format(
            name=content.title,
            tagline=content.tagline,
            top_highlight=content.highlights[0] if content.highlights else "",
            repo_url=content.repo_url,
            hashtags=hashtags,
        )
        if len(candidate) <= 280:
            tweet = candidate
            break

    # Fallback: minimal tweet guaranteed to fit
    if not tweet:
        tweet = _truncate(
            f"{content.title}: {content.tagline}\n\n{content.repo_url}",
            280,
        )

    draft = f"# Twitter/X Single Post\n\n{tweet}\n\n---"

    return {"twitter_single.md": draft}


def humanize_for_discord(content: ReadmeContent) -> dict[str, str]:
    """Generate a Discord message draft.

    Returns ``{"discord.md": formatted_content}``.
    Format matches ``_parse_discord_draft()`` in ``post.py``.
    """
    highlights_md = "\n".join(
        f"\u2022 {h}" for h in content.highlights
    ) if content.highlights else ""

    tech_md = ", ".join(content.tech_stack) if content.tech_stack else ""

    message_parts = [
        f"**{content.title}** \u2014 {content.tagline}",
        "",
        content.description,
        "",
    ]

    if highlights_md:
        message_parts.extend(["**Highlights:**", highlights_md, ""])

    if tech_md:
        message_parts.extend([f"**Built with:** {tech_md}", ""])

    message_parts.extend([
        f"\U0001f517 **GitHub:** <{content.repo_url}>",
        "",
        "Feedback welcome! \U0001f64f",
    ])

    message = "\n".join(message_parts)

    draft = (
        "# Discord Message\n\n"
        "**Post this in #showcase or #projects channels:**\n\n"
        f"{message}\n\n"
        "---"
    )

    return {"discord.md": draft}


def humanize_for_hackernews(content: ReadmeContent) -> dict[str, str]:
    """Generate a Hacker News Show HN draft.

    Returns ``{"hackernews.md": formatted_content}``.
    Format matches ``_parse_hn_draft()`` in ``post.py``.
    """
    short_desc = content.description.split(".")[0].strip() if content.description else content.tagline

    title = _pick(
        HN_TITLES,
        name=content.title,
        tagline=content.tagline,
        short_desc=short_desc,
    )
    title = _truncate(title, 80)

    highlights_text = (
        "\n".join(f"- {h}" for h in content.highlights)
        if content.highlights
        else ""
    )

    body_parts = [content.description]

    if highlights_text:
        body_parts.extend(["", f"Key features:\n{highlights_text}"])

    body_parts.extend([
        "",
        f"GitHub: {content.repo_url}",
        "",
        "Would love feedback from the HN community!",
    ])

    body = "\n".join(body_parts)

    draft = (
        "# Hacker News \u2014 Show HN Post\n\n"
        f"**Title:** {title}\n\n"
        f"**URL:** {content.repo_url}\n\n"
        "**Text (optional, for Show HN):**\n\n"
        f"{body}\n\n"
        "---"
    )

    return {"hackernews.md": draft}


def generate_all_drafts(
    content: ReadmeContent,
    subreddits: list[str] | None = None,
) -> dict[str, str]:
    """Generate drafts for all platforms.

    Calls each platform humanizer and merges the results into a single dict
    of ``filename -> content``.
    """
    drafts: dict[str, str] = {}
    drafts.update(humanize_for_reddit(content, subreddits=subreddits))
    drafts.update(humanize_for_devto(content))
    drafts.update(humanize_for_twitter(content))
    drafts.update(humanize_for_discord(content))
    drafts.update(humanize_for_hackernews(content))
    return drafts
